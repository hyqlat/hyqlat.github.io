# from scholarly import scholarly
# import jsonpickle
# import json
# from datetime import datetime
# import os

# author: dict = scholarly.search_author_id(os.environ['GOOGLE_SCHOLAR_ID'])
# scholarly.fill(author, sections=['basics', 'indices', 'counts', 'publications'])
# name = author['name']
# author['updated'] = str(datetime.now())
# author['publications'] = {v['author_pub_id']:v for v in author['publications']}
# print(json.dumps(author, indent=2))
# os.makedirs('results', exist_ok=True)
# with open(f'results/gs_data.json', 'w') as outfile:
#     json.dump(author, outfile, ensure_ascii=False)

# shieldio_data = {
#   "schemaVersion": 1,
#   "label": "citations",
#   "message": f"{author['citedby']}",
# }
# with open(f'results/gs_data_shieldsio.json', 'w') as outfile:
#     json.dump(shieldio_data, outfile, ensure_ascii=False)


# from scholarly import scholarly, ProxyGenerator
# import json
# from datetime import datetime
# import os

# # Setup ProxyGenerator
# pg = ProxyGenerator()
# pg.FreeProxies()  # Use free proxies (alternatively, configure proxies specific to your environment)
# scholarly.use_proxy(pg)

# # Start crawling
# author = scholarly.search_author_id(os.environ['GOOGLE_SCHOLAR_ID'])
# scholarly.fill(author, sections=['basics', 'indices', 'counts', 'publications'])
# author['updated'] = str(datetime.now())
# author['publications'] = {v['author_pub_id']: v for v in author['publications']}

# os.makedirs('results', exist_ok=True)
# with open('results/gs_data.json', 'w') as outfile:
#     json.dump(author, outfile, ensure_ascii=False)

# shieldio_data = {
#     "schemaVersion": 1,
#     "label": "citations",
#     "message": f"{author.get('citedby', 0)}",
# }
# with open('results/gs_data_shieldsio.json', 'w') as outfile:
#     json.dump(shieldio_data, outfile, ensure_ascii=False)

import os
import json
import time
from datetime import datetime
from scholarly import scholarly, ProxyGenerator

def main():
    # 1) 环境变量防御性读取，缺失就早失败、给清晰提示
    scholar_id = os.environ.get('GOOGLE_SCHOLAR_ID')
    if not scholar_id:
        raise SystemExit("❌ 缺少环境变量 GOOGLE_SCHOLAR_ID，请在 Actions Secrets/Env 中配置")

    # 2) 代理：CI 上 FreeProxies 基本无效，建议用你自己稳定代理
    #    pg.SingleProxy(http="http://user:pass@host:port")
    #    或者干脆不用代理、靠重试 + 限速（见下）
    pg = ProxyGenerator()
    try:
        pg.FreeProxies()
        scholarly.use_proxy(pg)
    except Exception as e:
        print(f"⚠️ 代理初始化失败，降级为直连: {e}")

    # 3) 整个抓取包在重试里，scholarly 在 CI 上经常第一次就挂
    author = None
    for attempt in range(3):
        try:
            author = scholarly.search_author_id(scholar_id)
            scholarly.fill(author,
                           sections=['basics', 'indices', 'counts', 'publications'])
            break
        except Exception as e:
            print(f"⚠️ 第 {attempt+1} 次抓取失败: {e}")
            time.sleep(15)   # 退避，别把 Scholar 逼急

    if author is None:
        raise SystemExit("❌ 3 次重试后仍无法抓取，终止")

    # 4) 防御性处理 publications 可能缺失
    pubs = author.get('publications', []) or []
    author['publications'] = {v['author_pub_id']: v for v in pubs if 'author_pub_id' in v}
    author['updated'] = str(datetime.now())

    # 5) 修复缩进 + 写文件
    os.makedirs('results', exist_ok=True)
    with open('results/gs_data.json', 'w', encoding='utf-8') as f:
        json.dump(author, f, ensure_ascii=False)

    shieldio_data = {
        "schemaVersion": 1,
        "label": "citations",
        "message": str(author.get('citedby', 0)),
    }
    with open('results/gs_data_shieldsio.json', 'w', encoding='utf-8') as f:
        json.dump(shieldio_data, f, ensure_ascii=False)

    print(f"✅ 完成，被引数: {author.get('citedby', 0)}")

if __name__ == '__&#8203;main__':
    main()
