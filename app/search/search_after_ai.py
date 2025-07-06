from concurrent.futures import ThreadPoolExecutor
import time
from urllib.parse import urlparse
import traceback
import sys
from typing import List, Dict, Tuple
from pathlib import Path

from openai import OpenAI

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from app.search.search_searxng_api import search_api_worker
from app.search.models import SearchResults,SearchResult,SearchRequest
from app.utils.tools import get_time, response2json
from app.utils.black_url import URL_BLACKLIST
from app.utils.compress_content import compress_url_content
from config.logging_config import logger
from config import base_config as config
from app.utils.prompt import RELEVANCE_EVALUATION_PROMPT
    

# 日志配置在 config/logging_config.py 中统一管理

RELEVANCE_THRESHOLD = 0  # 相关性阈值,低于此分数的结果将被过滤
MAX_RETRIES = 3  # 最大重试次数
BATCH_SIZE = 15
# OpenAI 客户端初始化
client = OpenAI(
    api_key=config.SEARCH_KEYWORD_API_KEY,
    base_url=config.SEARCH_KEYWORD_API_URL
)

def is_duplicate(new_result, existing_results):
    """判断搜索结果是否重复"""
    # 这里可以引入一些判断规则,比如有些支持多语言的文档,url最后一个一般是相同的,通过前面语言代码区分不同语言,但是不好判断容易误判( 

    # def normalize_url(url):
    #     parsed = urlparse(url)
    #     domain = parsed.netloc
    #     path = parsed.path.rstrip('/')
    #     key_part = ''
    #     if path:
    #         path_parts = path.split('/')
    #         # 取路径中的最后一个非空部分作为标识
    #         if path_parts:
    #             key_part = path_parts[-1] if path_parts[-1] else (path_parts[-2] if len(path_parts) > 1 else '')
    #     return f"{domain}/{key_part}"
    
    # new_url_norm = normalize_url(new_result['url'])
    new_title = new_result['title'].strip() if 'title' in new_result else ''
    
    for result in existing_results:
        # if normalize_url(result['url']) == new_url_norm:
        #     return True
        if result.get('title', '').strip() == new_title and new_title:
            return True
            
    return False

def evaluate_single_batch(batch_idx : int, batch : List[Dict], search_purpose : str):
    """评估单批次搜索结果的相关性"""
    client = OpenAI(
        api_key=config.EVALUATE_API_KEY,
        base_url=config.EVALUATE_API_URL
    )
    # 构造格式化后的结果文本
    formatted_results = [
        f"索引 {idx}:\n标题: {result.get('title', '无标题')}\n内容摘要: {result.get('content', '')[:200]}\nURL: {result.get('url', '')}"
        for idx, result in enumerate(batch)
    ]
    results_text = "\n".join(formatted_results)
    evaluation_prompt = RELEVANCE_EVALUATION_PROMPT.substitute(
        current_time=get_time(),
        search_purpose=search_purpose,
        results_text=results_text,
        batch_size=len(batch)
    )

    retry_count = 0
    scores = {}
    success = False

    while retry_count < MAX_RETRIES and not success:
        try:
            messages = [{"role": "user", "content": evaluation_prompt}]
            response = client.chat.completions.create(
                model=config.EVALUATE_MODEL,
                messages=messages,
                temperature=0.1,
                stream=False
            )
            response_text = response.choices[0].message.content.strip()
            scores_dict = response2json(response_text)
            logger.info(f"批次 {batch_idx} 评分结果 (尝试 {retry_count+1}): {scores_dict}")

            # 检查输出是否包含所有索引
            if len(scores_dict) != len(batch):
                raise ValueError(f"输出长度 {len(scores_dict)} 与输入长度 {len(batch)} 不匹配")

            # 转换为全局索引和标准分数
            for key, value in scores_dict.items():
                try:
                    scores[key] = float(value)
                except (ValueError, TypeError) as e:
                    logger.warning(f"转换评分时出错: {e}, key={key}, value={value}")
            success = True

        except Exception as e:
            logger.error(f"批次 {batch_idx} 评估时出错: {e}")
            logger.error(traceback.format_exc())
            retry_count += 1

    # 多次尝试后仍未成功则采用默认评分
    if not success:
        logger.warning(f"批次 {batch_idx} 在 {MAX_RETRIES} 次尝试后仍未获取评分,使用默认评分")
        for idx, result in enumerate(batch):
            global_idx = batch_idx * 10 + idx
            scores[global_idx] = result.get('score', 3)
    results_score = []
    for idx,tmp in enumerate(batch):
        tmp["relevance_score"] = scores[list(scores.keys())[idx]]
        results_score.append(tmp)
    return results_score


def evaluate_relevance(search_purpose : str, search_results :List[Dict]):
    """使用多线程并发评估搜索结果的相关性和重要性"""
    if not search_results:
        return []
    
    # 将搜索结果分割 分批进行判断
    batches = []
    for i in range(0, len(search_results), BATCH_SIZE):
        batches.append(search_results[i:i+BATCH_SIZE])
    logger.info(f"将 {len(search_results)} 个结果分为 {len(batches)} 批进行评估")
    
    # 使用线程池并发处理评估任务
    with ThreadPoolExecutor(max_workers=min(config.EVALUATE_THREAD_NUM, len(batches))) as executor:
        futures = []
        for i, batch in enumerate(batches):
            futures.append(executor.submit(evaluate_single_batch, i, batch, search_purpose))
        
        # 收集结果
        results_score_all = []
        for future in futures:
            try:
                # results_score = future.result()
                results_score_all += future.result()
            except Exception as e:
                traceback.print_exc()
                logger.error(f"获取评估结果时出错: {str(e)}")
                logger.error(traceback.format_exc())
    
    # 按评分降序排序
    # sorted_scores = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)
    logger.info(f"评估完成,得到 {len(results_score_all)} 个评分结果")
    return results_score_all

def search_ai(search_request: SearchRequest, deep: bool = True) -> SearchResults:

    if deep:
        logger.info("详细搜索模式")
    else:
        logger.info("简易搜索模式")
    # time.sleep(10)
    start_time = time.time()
    # 对搜索引擎返回的内容进行去重得到的结果
    new_results = []
    max_search_results = search_request.max_search_results
    search_purpose = search_request.search_purpose
    time_page = search_request.time_page
    logger.info(f"开始搜索 - 目的: {search_purpose}")
    
    with ThreadPoolExecutor(max_workers=config.SEARCH_API_LIMIT) as executor:
        futures = []
        for data in search_request.query_keys:
            query = data.key
            language = data.language
            logger.info(f"搜索关键词: {query}, 语言: {language}, 时间范围: {time_page}")
            if query and language:
                futures.append(executor.submit(search_api_worker, query, language, time_page))
        
        # 收集搜索结果
        for future in futures:
            try:
                results = future.result()
                
                # 添加结果,同时进行去重
                for result in results:
                    if not is_duplicate(result, new_results):
                        new_results.append(result)
            except Exception as e:
                logger.error(f"处理搜索结果时出错: {str(e)}")
                logger.error(traceback.format_exc())
    if URL_BLACKLIST:
        unique_results = [
            result for result in new_results
            if not any(result.get('url').startswith(prefix) for prefix in URL_BLACKLIST)
        ]
    else:
        unique_results = new_results
    
    logger.info(f"搜索完成,处理后共有 {len(unique_results)} 个结果,黑名单排除了{len(new_results)-len(unique_results)}个结果")
    if len(unique_results) > 50:
        unique_results = unique_results[:50]
        logger.info("搜索结果过多,仅取前50个结果")
    if not unique_results:
        logger.warning("没有找到任何搜索结果")
        return {}
    
    try:
        # 评估结果的相关性和重要性
        results_score_all = evaluate_relevance(search_purpose, unique_results)
        top_results = sorted(results_score_all, key=lambda x:x['relevance_score'], reverse=True)
        top_results = top_results[:max_search_results:]
        for result in top_results:
            logger.info(
                "标题: %s, 相关性分数: %s, URL: %s",
                result['title'],
                result['relevance_score'],
                result['url'],
            )
    except Exception as e:
        logger.error(f"相关性评估出错,使用原始分数排序: {str(e)}")
        logger.error(traceback.format_exc())
        return {}    
    
    logger.info(f"筛选得到 {len(top_results)} 个相关结果")
    
    if not top_results:
        logger.warning("没有找到相关结果")
        return {}
    if deep:
        deepscan_results = deepscan(top_results, search_request)
        search_time = time.time() - start_time
        logger.info(f"搜索耗时: {search_time:.2f} 秒")
        
        return deepscan_results
    else:
        search_results = SearchResults(search_request=search_request)
        for i, result in enumerate(top_results):
                    if result:
                        title = result.get('title', '')
                        content = result.get('content', '')
                        url = result.get('url', '')
                        search_results.add_result(SearchResult(title=title,content=content,url=url))
        # print(response_new)
        return search_results


def deepscan(search_response: list, search_request: SearchRequest) -> SearchResults:
    """获取网页的内容"""
    logger.info(f"开始深度扫描 {len(search_response)} 个URL")
    search_results_deepscan = SearchResults(search_request=search_request)
    search_purpose = search_request.search_purpose
    # 使用多线程并发处理URL内容获取
    if search_response:
        with ThreadPoolExecutor(max_workers=config.CRAWL_THREAD_NUM) as executor:
            futures = {}
            for i, result in enumerate(search_response):
                url = result['url']
                title = result['title'] + "\n" + result['content']
                futures[executor.submit(compress_url_content, url, search_purpose, title)] = i
            
            # 收集结果并处理可能的错误
            url_contents = [None] * len(search_response)
            for future in futures:
                idx = futures[future]
                try:
                    url_contents[idx] = future.result()
                except Exception as e:
                    logger.error(f"获取URL内容失败 ({search_response[idx]['url']}): {str(e)}")
                    logger.error(traceback.format_exc())
                    url_contents[idx] = None
    
        logger.info("URL内容获取完毕")
        
        # 准备结构化结果
        results_with_content = []
        for result, content in zip(search_response, url_contents):
            result_copy = result.copy()
            if content:
                result_copy['mini_content'] = result.get('content', '')
                result_copy['content'] = content
            results_with_content.append(result_copy)
        for i, result in enumerate(results_with_content):
            if result:  # 确保结果存在
                url = result.get('url', '')
                content = result.get('content', '')
                title = result.get('title', '无标题')
                relevance_score = result.get('relevance_score', 0)
                search_results_deepscan.add_result(SearchResult(url,title,content,relevance_score))
    return search_results_deepscan

if __name__ == "__main__":
    # 示例使用
    querys = [
        {
            "keys": "2025 LPL春季赛季后赛赛程",
            "language": "zh-CN"
        },
        {
            "keys": "2025年LPL季后赛时间表",
            "language": "zh-CN"
        },
        {
            "keys": "2025 LPL第一阶段淘汰赛日程",
            "language": "zh-CN"
        }
    ]
    search_purpose = "了解2025年LPL春季赛季后赛的具体赛程安排和比赛时间"
    search_request = [SearchRequest(query['keys'],query['language'],[0, 0, 0],search_purpose) for query in querys]
    result = search_ai(search_request,deep=False)
    logger.info(result.to_str())
    logger.info(result.get_urls())
