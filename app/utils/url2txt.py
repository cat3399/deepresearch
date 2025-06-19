import sys
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

from config.base_config import FIRECRAWL_API_URL,FIRECRAWL_API_KEY,CRAWL4AI_API_URL, AVAILABLE_EXTENSIONS
from config.logging_config import logger
from app.utils.tools import download_file,extract_text_from_file

def by_firecrawl(url: str, server_url: str = FIRECRAWL_API_URL) -> Optional[str]:
    try:
        scrape_url = f"{server_url}/v1/scrape"
        payload = {
            "url": url,
            "onlyMainContent": True,
            "formats": ["markdown"],
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
        }
        
        response = requests.request("POST", scrape_url, json=payload, headers=headers,timeout=20)
        # print(response.text)
        # print(response.status_code)
        response.raise_for_status()  # 检查HTTP错误
        
        data_json = json.loads(response.text)
        markdown_str = data_json['data']['markdown']
        return markdown_str
        
    except Exception as e:
        logger.error(f"firecrawl抓取 {url} 失败: {str(e)}")
        return 'error'

def by_crawl4ai(url: str, server_url: str = CRAWL4AI_API_URL) ->str:
    headers = {"Authorization": "Bearer cat3399"}
    crawl_paylod = {
        "urls" : [f"{url}"], 
    }
    response = requests.post(
        server_url,
        headers=headers,
        json=crawl_paylod
    )
    rsp_json = response.json()
    result_makrdown = rsp_json["results"][0]["markdown"]["raw_markdown"]
    return result_makrdown


# def by_crawl4ai(url: str, server_url: str = CRAWL4AI_API_URL) -> Optional[str]:
#     try:
#         crawl_url = f"{server_url}/crawl"
#         data = {"url": url}
#         response = requests.post(crawl_url, json=data, timeout=35)
#         # print(response.text)
#         return response.json()['markdown']   
#     except Exception as e:
#         logger.error(f"crawl4ai抓取 {url} 失败: {str(e)}")
#         return 'error'

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
    url = url.strip(' ')
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
        try:
            # 尝试使用firecrawl抓取
            if FIRECRAWL_API_URL:
                result = by_firecrawl(url)
                # print(result)
                if len(result) > 1000 and result != 'error':
                    logger.info(f'使用firecrawl抓取 {url} 成功 \n')
                    return result
                elif result != 'error' and len(result) > len(best_result):
                    best_result = result  # 保存最佳结果
                
            if CRAWL4AI_API_URL:
                # 尝试使用crawl4ai抓取
                result = by_crawl4ai(url)
                # print(result)
                if result and result != 'error':
                    if len(result) > 1000:
                        logger.info(f'使用crawl4ai抓取 {url} 成功 \n')
                        return result
                    elif len(result) > len(best_result):
                        best_result = result  # 保存最佳结果
                        logger.info('保存crawl4ai结果,但继续尝试获取更好的结果')
                    else:
                        logger.info('crawl4ai结果过短,继续尝试')
                
                # 如果两种方法都没有产生足够长的结果,增加尝试次数
                attempt_count += 1
                if attempt_count < max_attempts:
                    logger.info(f"结果长度不足,第 {attempt_count+1} 次尝试抓取...")
                
        except Exception as e:
            logger.error(f"抓取失败: {str(e)}")
            attempt_count += 1
    
    # 如果没有找到长度>1000的结果,但有其他结果,返回最佳结果
    if best_result:
        logger.info(f"未找到长度>1000的结果,返回最佳可用结果(长度:{len(best_result)})")
        return best_result
            
    return ''  # 如果所有尝试都失败,返回空字符串
# 使用示例
if __name__ == "__main__":
    test_url = "https://xxgk.nepu.edu.cn/2025niandongbeishiyoudaxuebumenyusuan.pdf"
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