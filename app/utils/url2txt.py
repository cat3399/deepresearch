import sys
import time
import requests
import json
from typing import Optional
import  os
from pathlib import Path
from dotenv import load_dotenv

# 获取项目根目录
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# 将项目根目录添加到sys.path
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from config.base_config import FIRECRAWL_API_URL,FIRECRAWL_API_KEY,CRAWL4AI_API_URL, AVAILABLE_EXTENSIONS, JINA_API_KEY, JINA_API_URL
from config.logging_config import logger
from app.utils.tools import download_file,extract_text_from_file

MIN_RESULT_LEN = 1000

def by_firecrawl(url: str, server_url: str = FIRECRAWL_API_URL) -> str:
    scrape_url = f"{server_url}/v1/scrape"
    payload = {
        "url": url,
        "onlyMainContent": True,
        "formats": ["markdown"],
    }
    
    headers = {
        "Content-Type": "application/json",
    }
    if FIRECRAWL_API_KEY:
        headers["Authorization"] = f"Bearer {FIRECRAWL_API_KEY}"
    response = requests.post(scrape_url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    
    data_json = json.loads(response.text)
    markdown_str = data_json['data']['markdown']
    return markdown_str

def by_crawl4ai(url: str, server_url: str = CRAWL4AI_API_URL) ->str:
    # headers = {"Authorization": "Bearer cat3399"}
    crawl_paylod = {
        "urls" : [f"{url}"], 
    }
    response = requests.post(
        server_url,
        # headers=headers,
        json=crawl_paylod
    )
    response.raise_for_status()
    rsp_json = response.json()
    result_makrdown = rsp_json["results"][0]["markdown"]["raw_markdown"]
    return result_makrdown

def by_jina(url: str, server_url: str = JINA_API_URL) -> str:
    payload = {
        "url": url,
    }
    headers = {
        "Content-Type": "application/json",
    }
    if JINA_API_KEY:
        headers["Authorization"] = f"Bearer {JINA_API_KEY}"
    response = requests.post(server_url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text

def url_to_markdown(url: str) -> Optional[str]:
    """
    从给定URL抓取内容并转换为Markdown格式
    
    Args:
        url: 要抓取的目标网页URL    
    Returns:
        str: Markdown格式的内容 如果抓取失败则返回空字符串
    """
    attempt_count = 0
    max_attempts = 2
    best_result = ''  # 存储最佳结果
    if not url:
        return ""
    url = url.strip(' ')
    url = url.lower()
    # Jina支持直接读取
    if not JINA_API_URL:
        if url.endswith(tuple(AVAILABLE_EXTENSIONS)):
            logger.info(f"下载文件 { url.rsplit('//')[-1] } 中...")
            file_name = download_file(url)
            if file_name:
                # 如果是文件,直接提取文本
                logger.info(f"下载文件 { url.rsplit('//')[-1] } 成功")
                result = extract_text_from_file(file_name)            
                return result
            else:
                logger.warning(f"下载文件 { url.rsplit('//')[-1] } 失败!")
                return "提取内容失败!"

    while attempt_count < max_attempts:
        attempt_count += 1  # 在循环开始就增加计数
        try:
            # firecrawl
            if FIRECRAWL_API_URL:
                try:
                    result = by_firecrawl(url)
                    if result and result != 'error' and len(result) > MIN_RESULT_LEN:
                        logger.info(f'使用firecrawl抓取 {url} 成功')
                        return result
                    elif result and len(result) > len(best_result):
                        best_result = result
                except Exception as e:
                    logger.error(f"Firecrawl抓取失败: {str(e)}")

            # crawl4ai 
            if CRAWL4AI_API_URL:
                try:
                    result = by_crawl4ai(url)
                    if result and result != 'error' and len(result) > MIN_RESULT_LEN:
                        logger.info(f'使用crawl4ai抓取 {url} 成功')
                        return result
                    elif result and len(result) > len(best_result):
                        best_result = result
                        logger.info('保存crawl4ai结果,继续尝试获取更好结果')
                except Exception as e:
                    logger.error(f"Crawl4ai抓取失败: {str(e)}")

            # jina
            if JINA_API_URL:
                try:
                    result = by_jina(url)
                    if result and result != 'error' and len(result) > MIN_RESULT_LEN:
                        logger.info(f'使用Jina抓取 {url} 成功')
                        return result
                    elif result and len(result) > len(best_result):
                        best_result = result
                        logger.info('保存Jina结果,继续尝试获取更好结果')
                except Exception as e:
                    logger.error(f"Jina抓取失败: {str(e)}")

            if attempt_count < max_attempts:
                logger.info(f"抓取过程出现问题,第 {attempt_count+1} 次尝试抓取...")
                time.sleep(1)  # 添加重试延迟

        except Exception as e:
            logger.error(f"抓取过程发生未知错误: {str(e)}")
            if attempt_count < max_attempts:
                time.sleep(1)

    if best_result:
        logger.info(f"返回最佳可用结果(长度:{len(best_result)})")
        return best_result

    return ''

# 使用示例
if __name__ == "__main__":
    test_url = "https://ai.google.dev/gemini-api/docs/music-generation?hl=zh-cn"
    result = url_to_markdown(test_url)
    logger.info(result)
    # if result:
    #     print(result)
    #     # 可选：保存到文件
    #     with open('output.md', 'w', encoding='utf-8') as f:
    #         f.write(result)
    # r = by_crawl4ai(test_url)
    # print(r)
    # print('---------------------------------------')
    # print('---------------------------------------')
    # print('---------------------------------------')
    # print('---------------------------------------')
    # print('---------------------------------------')
    # r = by_firecrawl(test_url)
    # print(r)