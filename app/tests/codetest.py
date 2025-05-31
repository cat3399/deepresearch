import requests
import logging
import re  # re 仍然保留，以防未来有其他正则需求，但当前过滤不再使用它
import traceback
import time
import sys
from pathlib import Path

# --- 配置和路径设置 ---
# 将项目根目录添加到sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from app.search.search_searxng_api import search_api_worker
from app.search.search_after_ai import is_duplicate

new_results = []


results = search_api_worker(query="gpt o4mini",language='en-US')
results2 = search_api_worker(query="openai chatgpt o4-mini",language='en-US')
results = results + results2

for i,result in enumerate(results):
    # print(f"网页{i+1}")
    # print(result['url'])
    # print(result['title'])
    # print(result['content'])
    # print(result["score"])
    # print("-"*20)
    if not is_duplicate(result, new_results):
        new_results.append(result)

    # new_results.append()
# print(results)

for i,result in enumerate(new_results):
    print(f"网页{i+1}")
    print(result['url'])
    print(result['title'])
    print(result['content'])
    print(result["score"])
    print("-"*20)

print(len(results))
print(len(new_results))
