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



import os, json, time
from datetime import datetime
from scholarly import scholarly, ProxyGenerator

os.makedirs('results', exist_ok=True)   # ← 提前，先建目录

sid = os.environ.get('GOOGLE_SCHOLAR_ID')
if not sid:
    raise SystemExit("❌ 缺少 GOOGLE_SCHOLAR_ID")

pg = ProxyGenerator()
try:
    pg.FreeProxies(); scholarly.use_proxy(pg)
except Exception as e:
    print("⚠️ 代理失败，直连:", e)

author = None
for i in range(4):
    try:
        author = scholarly.search_author_id(sid)
        scholarly.fill(author, sections=['basics','indices','counts','publications'])
        break
    except Exception as e:
        print(f"⚠️ 第{i+1}次抓取失败: {e}")
        time.sleep(20)

if author is None:
    raise SystemExit("❌ 抓取失败，终止")

author['updated'] = str(datetime.now())
pubs = author.get('publications', []) or []
author['publications'] = {v['author_pub_id']: v for v in pubs if 'author_pub_id' in v}

with open('results/gs_data.json', 'w', encoding='utf-8') as f:
    json.dump(author, f, ensure_ascii=False)
with open('results/gs_data_shieldsio.json', 'w', encoding='utf-8') as f:
    json.dump({"schemaVersion":1,"label":"citations","message":str(author.get('citedby',0))}, f, ensure_ascii=False)
print("✅ 完成，被引:", author.get('citedby', 0))
