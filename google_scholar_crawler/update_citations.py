"""
本地运行版：抓 Google Scholar 引用数据 → 写入 results/ → 可选自动推送到 google-scholar-stats 分支

为什么放本地跑：
  GitHub Actions 的 runner 是机房 IP，Scholar 风控必拦；本地家宽 IP + 大哥云节点才跑得通。

用法（PowerShell）：
  # 1. 先确认同目录下已有 requirements 依赖（scholarly / bibtexparser<2 / httpx<0.28）
  # 2. 设置环境变量
  $env:GOOGLE_SCHOLAR_ID = "你的Scholar作者ID"
  $env:PROXY_URL = "127.0.0.1:7897"        # 你的本地代理端口，不加 http://

  # 3. 干跑（只抓数据，不推送）
  python update_citations.py

  # 4. 抓完顺便推送到分支
  python update_citations.py --push

可选环境变量：
  PROXY_URL          本地代理 host:port。支持 http/socks5，默认按 http 处理
  PROXY_SCHEME       显式指定协议：http / socks5（默认 http）
  REPO_DIR           仓库根目录（默认为本脚本所在目录的上级）
  STATS_BRANCH       推送目标分支，默认 google-scholar-stats
  CITATION_SOURCE_LABEL  徽章 label，默认 citations
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import datetime

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
RETRIES = 4


def log(msg: str) -> None:
    print(msg, flush=True)


def check_proxy_ip() -> None:
    """通过代理查出口 IP，确认代理真的生效。"""
    proxy = os.environ.get("PROXY_URL", "").strip()
    if not proxy:
        log("⚠️  未设置 PROXY_URL，将直连（本地家宽 IP 有一定成功率，但容易被拦）")
        return

    scheme = os.environ.get("PROXY_SCHEME", "http").strip() or "http"
    proxy_url = f"{scheme}://{proxy}"
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url})
    )
    try:
        with opener.open("https://api.ipify.org", timeout=20) as r:
            ip = r.read().decode().strip()
        log(f"→ 代理已生效，出口 IP: {ip}")
    except Exception as e:
        log(f"⚠️  代理连通性检查失败: {e}")
        log("   请确认客户端已开启 HTTP/混合端口，且端口号正确")
        raise SystemExit(1)


def crawl() -> dict:
    """抓取作者数据，带重试。"""
    from scholarly import scholarly, ProxyGenerator

    sid = os.environ.get("GOOGLE_SCHOLAR_ID", "").strip()
    if not sid:
        log("❌ 缺少环境变量 GOOGLE_SCHOLAR_ID")
        raise SystemExit(1)

    # 代理配置（必须先于任何 scholar 请求）
    # 注意：scholarly 1.7.x 的 use_proxy(pg) 在 pg2 为空时，会新建一个 ProxyGenerator
    # 并强行调用 pm2.FreeProxies() 去拉免费代理列表。这一步在本地常常超时失败：
    #   fp.errors.FreeProxyException: Request to https://free-proxy-list.net/... failed
    # 即使我们只想用固定代理也会被它拖死。所以这里直接把 pm1/pm2 都设成同一个
    # 固定代理生成器，并自行重建 session，完全绕过 use_proxy()。
    proxy = os.environ.get("PROXY_URL", "").strip()
    if proxy:
        scheme = os.environ.get("PROXY_SCHEME", "http").strip() or "http"
        url = f"{scheme}://{proxy}"

        pg = ProxyGenerator()
        pg.SingleProxy(http=url, https=url)

        nav = getattr(scholarly, "_Scholarly__nav", None)
        if nav is None:
            log("❌ 无法取得 scholarly 内部 navigator，请检查 scholarly 版本")
            raise SystemExit(1)

        nav.pm1 = pg
        nav.pm2 = pg          # 关键：避免 use_proxy() 去拉 FreeProxies
        nav._session1 = pg.get_session()
        nav._session2 = pg.get_session()
        log(f"→ 使用固定代理 {url}（已跳过 FreeProxies 探测）")
    else:
        log("→ 未设代理，直连")

    author = None
    last_err = None
    for i in range(RETRIES):
        try:
            log(f"→ 第 {i + 1}/{RETRIES} 次抓取…")
            author = scholarly.search_author_id(sid)
            scholarly.fill(
                author,
                sections=["basics", "indices", "counts", "publications"],
            )
            log("✅ 抓取成功")
            break
        except Exception as e:
            last_err = e
            log(f"⚠️  失败: {e}")
            if i < RETRIES - 1:
                wait = 15 * (i + 1)
                log(f"   {wait}s 后重试…")
                time.sleep(wait)

    if author is None:
        log(f"❌ {RETRIES} 次重试后仍失败: {last_err}")
        log("   建议：换个节点重试 / 稍后再跑 / 或等几十秒再跑一次")
        raise SystemExit(1)

    pubs = author.get("publications", []) or []
    author["updated"] = str(datetime.now())
    author["publications"] = {
        v["author_pub_id"]: v for v in pubs if "author_pub_id" in v
    }
    return author


def write_files(author: dict) -> None:
    os.makedirs(RESULTS_DIR, exist_ok=True)

    with open(os.path.join(RESULTS_DIR, "gs_data.json"), "w", encoding="utf-8") as f:
        json.dump(author, f, ensure_ascii=False, indent=2)

    label = os.environ.get("CITATION_SOURCE_LABEL", "citations")
    with open(
        os.path.join(RESULTS_DIR, "gs_data_shieldsio.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(
            {
                "schemaVersion": 1,
                "label": label,
                "message": f"{author.get('citedby', 0)}",
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    log(f"→ 已写入 {RESULTS_DIR}")
    log(f"   被引: {author.get('citedby', 0)}")


def run(cmd: list, cwd: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, cwd=cwd, check=check, capture_output=True, text=True, encoding="utf-8"
    )


def push(author: dict) -> None:
    """把 results/ 推送到 STATS_BRANCH 分支（不影响你的主分支）。"""
    repo_dir = os.environ.get("REPO_DIR") or os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
    if not os.path.isdir(os.path.join(repo_dir, ".git")):
        log(f"❌ REPO_DIR 不是 git 仓库: {repo_dir}")
        raise SystemExit(1)

    branch = os.environ.get("STATS_BRANCH", "google-scholar-stats")
    rel = os.path.relpath(RESULTS_DIR, repo_dir).replace("\\", "/")

    log(f"→ 推送目标仓库: {repo_dir}")
    log(f"→ 目标分支: {branch}，路径: {rel}/")

    # 当前分支，稍后切回
    orig = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo_dir).stdout.strip()
    log(f"→ 当前分支: {orig}")

    # 工作区是否有未提交改动（避免影响用户正在进行的工作）
    dirty = run(["git", "status", "--porcelain"], repo_dir).stdout.strip()
    if dirty:
        log("⚠️  工作区有未提交改动，为安全起见不自动切换分支。")
        log("   请先提交或 stash，或手动执行推送。")
        raise SystemExit(1)

    # 暂存 results 到临时目录
    tmp = tempfile.mkdtemp(prefix="citation_")
    for fn in os.listdir(RESULTS_DIR):
        shutil.copy2(os.path.join(RESULTS_DIR, fn), tmp)

    try:
        # 切到分支（不存在则新建）
        exists = run(
            ["git", "rev-parse", "--verify", "--quiet", branch], repo_dir, check=False
        )
        if exists.returncode == 0:
            run(["git", "checkout", branch], repo_dir)
            # 拉取远端最新，避免 non-fast-forward
            run(["git", "pull", "--rebase", "origin", branch], repo_dir, check=False)
        else:
            run(["git", "checkout", "--orphan", branch], repo_dir)
            run(["git", "rm", "-rf", "--cached", "."], repo_dir, check=False)

        # 写入文件
        target = os.path.join(repo_dir, rel)
        os.makedirs(target, exist_ok=True)
        for fn in os.listdir(tmp):
            shutil.copy2(os.path.join(tmp, fn), target)

        run(["git", "add", f"{rel}"], repo_dir)
        staged = run(["git", "diff", "--cached", "--quiet"], repo_dir, check=False)
        if staged.returncode == 0:
            log("→ 没有变化，跳过提交")
        else:
            msg = f"Updated Citation Data ({author.get('citedby', 0)} citations)"
            run(["git", "commit", "-m", msg], repo_dir)
            run(["git", "push", "--force", "origin", f"HEAD:{branch}"], repo_dir)
            log(f"✅ 已推送到 {branch}")

            # 回到原分支
            if orig and orig != "HEAD" and orig != branch:
                run(["git", "checkout", orig], repo_dir)
                log(f"→ 已切回 {orig}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="本地抓取 Scholar 引用数据")
    ap.add_argument("--push", action="store_true", help="抓取后自动推送到目标分支")
    ap.add_argument("--skip-proxy-check", action="store_true", help="跳过代理连通性检查")
    args = ap.parse_args()

    if not args.skip_proxy_check:
        check_proxy_ip()

    author = crawl()
    write_files(author)

    if args.push:
        push(author)
    else:
        log("")
        log("💡 加 --push 参数可自动推送到分支")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n已取消")
        sys.exit(130)
