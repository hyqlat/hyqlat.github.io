"""
OpenAlex 版引用数据抓取（替代 scholarly / Google Scholar 方案）

输出与旧脚本完全一致：
  results/gs_data.json            —— 作者基础信息 + summary_stats + 出版物列表
  results/gs_data_shieldsio.json  —— shields.io 徽章数据（citations 数值）

环境变量（任选其一，优先级从上到下）：
  OPENALEX_AUTHOR_ID   OpenAlex 作者 ID，形如 A5023888391
  ORCID               形如 0000-0002-1825-0097（不带 https://orcid.org/ 也可以）
  AUTHOR_NAME         OpenAlex 免费文本搜索名（模糊，不保证唯一，仅作兜底）

可选：
  OPENALEX_API_KEY    OpenAlex 免费 API key（强烈建议！无 key 时全网络共享 $0.10/天额度，
                      极易 401；有 key 独享 $1/天。申请：https://openalex.org/settings/api ）
  OPENALEX_MAILTO     你的邮箱，写入 User-Agent 便于识别（建议填）
  CITATION_SOURCE_LABEL  徽章显示名，默认 citations
"""

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

BASE = "https://api.openalex.org"
TIMEOUT = 60
RETRIES = 4
PAGE_SIZE = 100  # 单页 200 时响应体可达数 MB，易触发读取截断，降到 100 更稳


def _get_json(url: str) -> dict:
    """带重试的 GET，自动附加 api_key / mailto。"""
    mailto = os.environ.get("OPENALEX_MAILTO")
    api_key = os.environ.get("OPENALEX_API_KEY")

    params = []
    if api_key:
        params.append(f"api_key={urllib.parse.quote(api_key)}")
    if mailto:
        params.append(f"mailto={urllib.parse.quote(mailto)}")
    if params:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}{'&'.join(params)}"

    ua = f"github-actions-citation-badge/1.0 ({mailto or 'no-mailto'})"
    last_err = None
    for i in range(RETRIES):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": ua})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last_err = e
            body = ""
            try:
                body = e.read().decode("utf-8", "ignore")[:300]
            except Exception:
                pass
            print(f"  ⚠️ HTTP {e.code}（第 {i + 1}/{RETRIES} 次）: {body}")
            if e.code == 401:
                print(
                    "     ↳ 401 通常是 OpenAlex 免费额度耗尽。请配置 OPENALEX_API_KEY "
                    "(https://openalex.org/settings/api ，免费 $1/天)，或明日额度重置后再试。"
                )
                break
            if i < RETRIES - 1:
                time.sleep(5 * (i + 1))
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            last_err = e
            print(f"  ⚠️ 请求失败（第 {i + 1}/{RETRIES} 次）: {e}")
            if i < RETRIES - 1:
                time.sleep(5 * (i + 1))
    raise RuntimeError(f"OpenAlex 请求最终失败: {url} -> {last_err}")


def resolve_author() -> dict:
    """按 OPENALEX_AUTHOR_ID -> ORCID -> AUTHOR_NAME 的顺序定位唯一作者。"""
    author_id = os.environ.get("OPENALEX_AUTHOR_ID", "").strip()
    orcid = os.environ.get("ORCID", "").strip()
    name = os.environ.get("AUTHOR_NAME", "").strip()

    if author_id:
        author_id = author_id.rstrip("/").split("/")[-1]
        print(f"→ 直接按 OpenAlex ID 查询: {author_id}")
        return _get_json(f"{BASE}/authors/{author_id}")

    if orcid:
        orcid = orcid.replace("https://orcid.org/", "").strip()
        print(f"→ 按 ORCID 查询: {orcid}")
        # orcid 过滤器同时匹配 primary 与 observed ORCID
        data = _get_json(f"{BASE}/authors?filter=orcid:{orcid}&per-page=5")
        hits = data.get("results") or []
        if not hits:
            raise SystemExit(f"❌ 在 OpenAlex 中找不到 ORCID={orcid} 对应的作者")
        if len(hits) > 1:
            print(f"  ⚠️ 命中 {len(hits)} 个作者，取第一个。建议改用 OPENALEX_AUTHOR_ID 精确指定：")
            for h in hits:
                print(f"     - {h['id']}  {h.get('display_name')}  works={h.get('works_count')}")
        return hits[0]

    if name:
        print(f"→ 按姓名搜索: {name}（模糊匹配，可能选错人）")
        q = urllib.parse.quote(name)
        data = _get_json(f"{BASE}/authors?search={q}&per-page=10")
        hits = data.get("results") or []
        if not hits:
            raise SystemExit(f"❌ 在 OpenAlex 中搜不到姓名: {name}")
        # 取被引最高、且有作品的候选人
        hits.sort(key=lambda a: (a.get("cited_by_count") or 0), reverse=True)
        for h in hits[:5]:
            print(f"     候选 {h['id']}  {h.get('display_name')}  cited={h.get('cited_by_count')}")
        return hits[0]

    raise SystemExit(
        "❌ 缺少作者标识。请至少配置下列之一：\n"
        "   OPENALEX_AUTHOR_ID（推荐） / ORCID / AUTHOR_NAME"
    )


def fetch_works(author_id: str, max_works: int = 0) -> list:
    """
    分页拉取该作者的作品。
    max_works > 0 时最多拉取这么多篇（0 表示全量）。
    徽章只需要 cited_by_count / h_index，作者对象里已自带，
    因此默认只拉少量作品用于生成出版物列表，避免长时间运行与额度浪费。
    """
    aid = author_id.rstrip("/").split("/")[-1]
    works = []
    page = 1
    total = None
    while True:
        url = f"{BASE}/works?filter=author.id:{aid}&per-page={PAGE_SIZE}&page={page}"
        data = _get_json(url)
        meta = data.get("meta") or {}
        if total is None:
            total = meta.get("count") or 0
            print(f"→ 该作者共有作品 {total} 篇")
        batch = data.get("results") or []
        works.extend(batch)
        if max_works and len(works) >= max_works:
            works = works[:max_works]
            break
        if not batch or len(batch) < PAGE_SIZE or len(works) >= total:
            break
        page += 1
        if page > 100:
            break
        time.sleep(0.2)
    print(f"→ 实际拉取作品 {len(works)} 篇")
    return works


def main() -> None:
    # 先建目录，保证即使后续失败目录也存在（避免 workflow 里 cd results 报错）
    os.makedirs("results", exist_ok=True)

    author = resolve_author()
    aid = author["id"]

    stats = author.get("summary_stats") or {}
    cited_by = author.get("cited_by_count") or 0
    print(
        f"→ 作者: {author.get('display_name')} ({aid})\n"
        f"   总被引: {cited_by} | works: {author.get('works_count')} | "
        f"h-index: {stats.get('h_index')} | i10: {stats.get('i10_index')}"
    )

    works = fetch_works(aid, max_works=int(os.environ.get("MAX_WORKS", "200")))

    # ---- 组装输出：结构与旧 gs_data.json 保持兼容 ----
    pubs = {}
    for w in works:
        wid = w.get("id") or ""
        key = wid.rstrip("/").split("/")[-1] or w.get("title", "")[:40]
        loc = w.get("primary_location") or {}
        src = (loc.get("source") or {}) if isinstance(loc, dict) else {}
        bib = w.get("biblio") or {}

        # 统一的作者字符串，方便前端直接用
        auth_names = []
        for a in w.get("authorships") or []:
            nm = (a.get("author") or {}).get("display_name")
            if nm:
                auth_names.append(nm)

        pubs[key] = {
            "author_pub_id": key,
            "bib": {
                "title": w.get("title") or w.get("display_name") or "",
                "pub_year": str(w.get("publication_year") or ""),
                "citation": str(w.get("cited_by_count") or 0),
                "author": ", ".join(auth_names),
                "venue": src.get("display_name") or "",
                "volume": bib.get("volume") or "",
                "issue": bib.get("issue") or "",
                "first_page": bib.get("first_page") or "",
                "last_page": bib.get("last_page") or "",
            },
            "num_citations": w.get("cited_by_count") or 0,
            "pub_url": (loc.get("landing_page_url") if isinstance(loc, dict) else "") or "",
            "doi": w.get("doi") or "",
            "type": w.get("type") or "",
            "publication_date": w.get("publication_date") or "",
            "source": "openalex",
        }

    out = {
        "name": author.get("display_name"),
        "openalex_id": aid,
        "orcid": author.get("orcid"),
        "affiliation": ", ".join(
            i.get("display_name", "")
            for i in (author.get("last_known_institutions") or [])
            if isinstance(i, dict)
        ),
        "citedby": cited_by,
        "citedby5y": 0,  # OpenAlex 无对应口径，占位保持字段存在
        "hindex": stats.get("h_index") or 0,
        "hindex5y": 0,
        "i10index": stats.get("i10_index") or 0,
        "i10index5y": 0,
        "works_count": author.get("works_count") or 0,
        "counts_by_year": author.get("counts_by_year") or [],
        "topics": [
            {"name": t.get("display_name"), "count": t.get("count")}
            for t in (author.get("topics") or [])
            if isinstance(t, dict)
        ],
        "publications": pubs,
        "source": "openalex",
        "updated": str(datetime.now()),
    }

    with open("results/gs_data.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    label = os.environ.get("CITATION_SOURCE_LABEL", "citations")
    shieldio = {
        "schemaVersion": 1,
        "label": label,
        "message": str(cited_by),
    }
    with open("results/gs_data_shieldsio.json", "w", encoding="utf-8") as f:
        json.dump(shieldio, f, ensure_ascii=False, indent=2)

    # 顺带生成 h-index 徽章，README 可直接用（不需要就删掉这行）
    with open("results/gs_data_hindex_shieldsio.json", "w", encoding="utf-8") as f:
        json.dump(
            {"schemaVersion": 1, "label": "h-index", "message": str(stats.get("h_index") or 0)},
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"✅ 完成。被引 {cited_by} | h-index {stats.get('h_index')} | 作品 {len(pubs)} 篇")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print(f"❌ 抓取失败: {e}", file=sys.stderr)
        sys.exit(1)
