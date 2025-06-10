import requests
import logging
import re  
import traceback
import time
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from app.utils.config import SEARXNG_URL
# 黑名单文件路径 (假设在项目根目录)
BLACKLIST_FILE = ROOT_DIR / 'blacklist.txt'
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MAX_RETRIES = 3  # 最大重试次数
if not SEARXNG_URL:
    SEARXNG_URL = "https://seek.nuer.cc/"
    # 使用 logging 记录，而不是 print
    logging.warning(f"未在环境变量中找到 SEARXNG_URL, 使用默认值: {SEARXNG_URL} (不保证长期可用)")

# --- 搜索工作函数 ---
def search_api_worker(query, language, time_page = [0,0,0]):
    """单个搜索API调用的工作函数,包含重试和黑名单过滤"""
    if not SEARXNG_URL:
        logging.error("SearxNG URL 未设置,请检查环境变量")
        return []

    params = {
        'q': query,
        'format': 'json',
        'language': language,
        'time_page': time_page,
        "engines": "bing,duckduckgo,google,wikipedia", # 引擎列表可以考虑也做成配置
    }

    retry_count = 0
    while retry_count < MAX_RETRIES:
        try:
            logging.info(f"正在搜索: '{query}' (语言:{language}, 时间页:{time_page})")
            response = requests.get(SEARXNG_URL, params=params, timeout=15)
            response.raise_for_status() # 检查 HTTP 错误状态码

            results = response.json().get('results', [])
            return results

        except requests.exceptions.RequestException as e: # 更具体的网络异常捕获
            retry_count += 1
            wait_time = 1 # 简单的固定等待时间，可以考虑指数退避
            log_level = logging.warning if retry_count < MAX_RETRIES else logging.error
            log_level(f"搜索关键词 '{query}' 时发生网络错误: {str(e)}. "
                      f"尝试次数 {retry_count}/{MAX_RETRIES}. "
                      f"{f'等待 {wait_time} 秒后重试...' if retry_count < MAX_RETRIES else '已达最大重试次数.'}")
            if logging.getLogger().isEnabledFor(logging.DEBUG): # 仅在 DEBUG 级别记录完整堆栈
                 logging.debug(traceback.format_exc())
            if retry_count < MAX_RETRIES:
                time.sleep(wait_time)
        except Exception as e: # 捕获其他可能的异常 (如 JSON 解析错误)
             # 对于非网络错误，通常不需要重试
            logging.error(f"处理关键词 '{query}' 的搜索结果时发生意外错误: {str(e)}")
            logging.error(traceback.format_exc())
            return [] # 出现意外错误，返回空列表

    # 如果循环结束仍未成功 (所有重试都失败)
    logging.error(f"搜索关键词 '{query}' 失败，已重试 {MAX_RETRIES} 次。")
    return []

# --- 示例用法 (如果需要直接运行此文件测试) ---
if __name__ == "__main__":
    # 配置日志记录器

    # 测试搜索
    test_query = "gpt o4mini vs gemini2.5 flash differences"
    results = search_api_worker(test_query, "en")
    for result in results:
        logging.info(result['url'])
