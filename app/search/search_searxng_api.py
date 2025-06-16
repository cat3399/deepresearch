import requests
import re  
import traceback
import time
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from config.logging_config import logger
from config.base_config import SEARXNG_URL,TAVILY_KEY

# 黑名单文件路径 (假设在项目根目录)
BLACKLIST_FILE = ROOT_DIR / 'blacklist.txt'
# 日志配置在 config/logging_config.py 中统一管理

MAX_RETRIES = 3  # 最大重试次数
# if not SEARXNG_URL:
#     SEARXNG_URL = "https://seek.nuer.cc/"
#     logger.warning(f"未在环境变量中找到 SEARXNG_URL, 使用默认值: {SEARXNG_URL} (不保证长期可用)")

def by_searxng(query, language, time_page = [0,0,0]):
    params = {
        'q': query,
        'format': 'json',
        'language': language,
        'time_page': time_page,
        "engines": "bing,duckduckgo,google,wikipedia",
    }

    retry_count = 0
    while retry_count < MAX_RETRIES:
        try:
            logger.info(f"正在搜索: '{query}' (语言:{language}, 时间页:{time_page})")
            response = requests.get(SEARXNG_URL, params=params, timeout=15)
            response.raise_for_status() # 检查 HTTP 错误状态码

            results = response.json().get('results', [])
            return results

        except requests.exceptions.RequestException as e: # 更具体的网络异常捕获
            retry_count += 1
            wait_time = 1 # 简单的固定等待时间，可以考虑指数退避
            log_level = logger.warning if retry_count < MAX_RETRIES else logger.error
            log_level(f"搜索关键词 '{query}' 时发生网络错误: {str(e)}. "
                      f"尝试次数 {retry_count}/{MAX_RETRIES}. "
                      f"{f'等待 {wait_time} 秒后重试...' if retry_count < MAX_RETRIES else '已达最大重试次数.'}")
            if logger.getLogger().isEnabledFor(logger.DEBUG): # 仅在 DEBUG 级别记录完整堆栈
                 logger.debug(traceback.format_exc())
            if retry_count < MAX_RETRIES:
                time.sleep(wait_time)
        except Exception as e: # 捕获其他可能的异常 (如 JSON 解析错误)
             # 对于非网络错误，通常不需要重试
            logger.error(f"处理关键词 '{query}' 的搜索结果时发生意外错误: {str(e)}")
            logger.error(traceback.format_exc())
            return [] # 出现意外错误，返回空列表

    # 如果循环结束仍未成功 (所有重试都失败)
    logger.error(f"搜索关键词 '{query}' 失败，已重试 {MAX_RETRIES} 次。")
    return []

def by_tavily(query, language, time_page = [0,0,0]):
    time_range = None
    time_page2time_range = {
        0:"d",
        1:"m",
        2:"y"
    }
    for i, j in enumerate(time_page):
        time_range = time_page2time_range[i] if j else time_range
    if time_page[0] >= 7 and sum(time_page[1:]) == 0:
        time_range = 'w'

    TAVILY_URL = "https://api.tavily.com/search"
    payload = {
        "query": query,
        "topic": "general",
        "search_depth": "basic",
        "chunks_per_source": 3,
        "max_results": 15,
        "time_range": time_range,
        "include_raw_content": False,
        "country": None
    }
    headers = {
        "Authorization": f"Bearer {TAVILY_KEY}",
        "Content-Type": "application/json"
    }

    retry_count = 0
    while retry_count < MAX_RETRIES:
        try:
            logger.info(f"Tavily 正在搜索: '{query}'")
            response = requests.post(TAVILY_URL, headers=headers, json=payload, timeout=15)
            response.raise_for_status() # 检查 HTTP 错误状态码

            results = response.json().get('results', [])
            return results

        except requests.exceptions.RequestException as e: # 更具体的网络异常捕获
            retry_count += 1
            wait_time = 1 # 简单的固定等待时间，可以考虑指数退避
            log_level = logger.warning if retry_count < MAX_RETRIES else logger.error
            log_level(f"搜索关键词 '{query}' 时发生网络错误: {str(e)}. "
                      f"尝试次数 {retry_count}/{MAX_RETRIES}. "
                      f"{f'等待 {wait_time} 秒后重试...' if retry_count < MAX_RETRIES else '已达最大重试次数.'}")
            if logger.getLogger().isEnabledFor(logger.DEBUG): # 仅在 DEBUG 级别记录完整堆栈
                 logger.debug(traceback.format_exc())
            if retry_count < MAX_RETRIES:
                time.sleep(wait_time)
        except Exception as e: # 捕获其他可能的异常 (如 JSON 解析错误)
             # 对于非网络错误，通常不需要重试
            logger.error(f"处理关键词 '{query}' 的搜索结果时发生意外错误: {str(e)}")
            logger.error(traceback.format_exc())
            return [] # 出现意外错误，返回空列表

    # 如果循环结束仍未成功 (所有重试都失败)
    logger.error(f"搜索关键词 '{query}' 失败，已重试 {MAX_RETRIES} 次。")
    return []

# --- 搜索工作函数 ---
def search_api_worker(query, language = "all", time_page = [0,0,0]):
    results = ""
    if SEARXNG_URL:
        logger.info(f"使用SeaXNG Search API")
        results = by_searxng(query=query,language=language,time_page=time_page)
    elif TAVILY_KEY:
        logger.info(f"使用Tavily Search API")
        results = by_tavily(query=query,language=language,time_page=time_page)

    return results
# --- 示例用法 (如果需要直接运行此文件测试) ---
if __name__ == "__main__":
    # 配置日志记录器

    # 测试搜索
    test_query = "gpt o4mini vs gemini2.5 flash differences"
    results = search_api_worker(test_query, "en")
    for result in results:
        logger.info(result['url'])
