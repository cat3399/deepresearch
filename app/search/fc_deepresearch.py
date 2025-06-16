import json
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from openai import OpenAI

# 将 ROOT_DIR 的解析和路径追加放在模块导入的更前面，以确保路径设置尽早生效
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from app.search.fc_search import search_core
from app.search.models import SearchRequest, SearchResult, SearchResults
from app.search.search_after_ai import deepscan, is_duplicate
from app.search.search_searxng_api import search_api_worker
from app.utils.black_url import URL_BLACKLIST
from config.base_config import (SEARCH_API_LIMIT,
                              SEARCH_KEYWORD_API_KEY, SEARCH_KEYWORD_API_URL,SEARCH_KEYWORD_MODEL,
                              EVALUATE_API_KEY, EVALUATE_API_URL, EVALUATE_MODEL, EVALUATE_THREAD_NUM
                              )
from config.logging_config import logger
from app.utils.prompt import (DEEPRESEARCH_FIRST_PROMPT,
                              DEEPRESEARCH_NEXT_PROMPT, GET_VALUE_URL_PROMPT)
from app.utils.tools import (format_search_plan, format_urls, get_time,
                             json2SearchRequests, response2json)

client = OpenAI(api_key=SEARCH_KEYWORD_API_KEY, base_url=SEARCH_KEYWORD_API_URL)
# 日志配置在 config/logging_config.py 中统一管理


def _search_valuable_results(
    search_request: SearchRequest, excluded_urls: list[str] = None
) -> SearchResults:
    if excluded_urls is None:
        excluded_urls = [""]  # 保持原有默认行为

    start_time = time.time()
    new_results = []
    if not search_request:
        logger.warning("搜索请求列表为空。")
        return SearchResults()

    search_purpose = search_request.search_purpose
    time_page = search_request.time_page
    logger.info(f"开始搜索 - 目的: {search_purpose}")

    with ThreadPoolExecutor(
        max_workers=SEARCH_API_LIMIT
    ) as executor:
        futures = []
        for data in search_request.query_keys:
            query = data.key
            language = data.language
            logger.info(
                f"搜索关键词: {query}, 语言: {language}, 时间范围: {time_page}"
            )
            if query and language:
                futures.append(
                    executor.submit(search_api_worker, query, language, time_page)
                )

        for future in futures:
            try:
                results = future.result()
                for result in results:
                    if not is_duplicate(result, new_results):
                        new_results.append(result)
            except Exception as e:
                logger.error(f"处理搜索结果时出错: {str(e)}")
                logger.error(traceback.format_exc())

    if URL_BLACKLIST:
        unique_results = [
            result
            for result in new_results
            if not any(
                result.get("url", "").startswith(prefix) for prefix in URL_BLACKLIST
            )
        ]
    else:
        unique_results = new_results

    if excluded_urls and excluded_urls != [""]: # 确保 excluded_urls 有实际内容
        stripped_excluded_set = {ex_url.strip() for ex_url in excluded_urls}
        unique_results = [
            result
            for result in unique_results
            if result.get("url", "").strip() not in stripped_excluded_set
        ]
    logger.info(f"排除了 {len(new_results)-len(unique_results)} 个结果")
    if not unique_results:
        logger.warning("没有找到任何搜索结果")
        # 返回一个空的 SearchResults 对象而不是字典
        return SearchResults(search_request=search_request, results=[])

    search_results_objects = [
        SearchResult(
            url=result.get("url", ""),
            title=result.get("title", ""),
            content=result.get("content", ""),
        )
        for result in unique_results
    ]
    return SearchResults(
        search_request=search_request,
        results=search_results_objects,
    )


def generate_search_plan(messages: list[dict], web_reference: str = "", previous_plan: str = "", previous_results: str = "", max_remaining_steps: int = 8) -> list:
    """
    生成搜索计划
    
    Args:
        messages: 用户消息
        web_reference: 初始搜索参考结果
        previous_plan: 上一轮搜索计划
        previous_results: 上一轮搜索结果
        max_remaining_steps: 剩余可执行步骤数
    
    Returns:
        list: 搜索计划步骤列表
    """
    if not previous_plan:
        # 生成第一个搜索计划
        prompt = DEEPRESEARCH_FIRST_PROMPT.substitute(
            current_time=get_time(),
            messages=str(messages),
            web_reference=web_reference
        )
    else:
        # 生成后续搜索计划
        prompt = DEEPRESEARCH_NEXT_PROMPT.substitute(
            current_time=get_time(),
            messages=str(messages),
            max_step=max_remaining_steps,
            previous_search_plan=previous_plan,
            previous_search_results=previous_results,
        )
    # print(prompt)
        # print("previous_plan",previous_plan)
    try:
        llm_rsp = client.chat.completions.create(
            model=SEARCH_KEYWORD_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            stream=False,
        )
        llm_rsp_content = llm_rsp.choices[0].message.content
        
        try:
            completion_tokens = llm_rsp.usage.completion_tokens
            total_tokens = llm_rsp.usage.total_tokens
            logger.debug(f"搜索计划生成输出tokens: {completion_tokens}")
            logger.debug(f"搜索计划生成总共花费tokens: {total_tokens}")
        except AttributeError:
            logger.debug("无法获取搜索计划生成的 token 使用情况。")
        
        parsed_rsp = response2json(llm_rsp_content)
        steps = parsed_rsp.get("steps", [])
        return steps
    except Exception as e:
        logger.error(f"生成搜索计划时出错: {str(e)}")
        return []


def _execute_search_plan(search_plan_step: dict, excluded_urls: list[str] = None) -> SearchResults:
    """
    执行单个搜索计划步骤
    
    Args:
        search_plan_step: 搜索计划步骤
        excluded_urls: 排除的URL列表
    
    Returns:
        SearchResults: 搜索结果
    """
    if excluded_urls is None:
        excluded_urls = [""]
    logger.info(f"执行搜索计划: {search_plan_step}")
    search_request = json2SearchRequests(search_plan_step)
    if not search_request:
        logger.warning("未能从计划中解析出有效的搜索请求。")
        return SearchResults()

    search_results = _search_valuable_results(
        search_request=search_request, excluded_urls=excluded_urls
    )
    if not search_results.results:
        logger.warning("未能从搜索中获取到结果。")
        return SearchResults(search_request=search_request, results=[])

    # 筛选有价值的URL
    max_valuable_urls = max(1, int(search_request.max_search_results / 2))
    value_url_prompt = GET_VALUE_URL_PROMPT.substitute(
        current_time=get_time(),
        search_results=search_results.to_str(),
        search_purpose=search_request.search_purpose,
        max_num=max_valuable_urls,
        search_restrictions=search_request.search_restrictions
    )
    # print("value_url_prompt: ",value_url_prompt)
    try:
        client = OpenAI(api_key=EVALUATE_API_KEY, base_url=EVALUATE_API_URL)
        llm_rsp_value = client.chat.completions.create(
            model=EVALUATE_MODEL,
            messages=[{"role": "user", "content": value_url_prompt}],
            temperature=0.1,
            stream=False,
        )

        try:
            completion_tokens_val = llm_rsp_value.usage.completion_tokens
            total_tokens_val = llm_rsp_value.usage.total_tokens
            logger.debug(f"价值URL筛选输出tokens: {completion_tokens_val}")
            logger.debug(f"价值URL筛选总共花费tokens: {total_tokens_val}")
        except AttributeError:
            logger.debug("无法获取价值URL筛选的 token 使用情况。")

        llm_rsp_content_value = llm_rsp_value.choices[0].message.content
        logger.debug(f"LLM返回的价值URL编号: {llm_rsp_content_value}")
        url_num_list_json = response2json(llm_rsp_content_value)
        valuable_results_data = []
        if url_num_list_json and isinstance(url_num_list_json, list):
            search_results_dict = search_results.to_dict()
            for url_num_str in url_num_list_json:
                key = f"网页{url_num_str}"
                if key in search_results_dict:
                    valuable_results_data.append(search_results_dict[key])
                else:
                    logger.warning(f"未能从搜索结果字典中找到键: {key}")
        else:
            logger.warning(f"LLM返回的价值URL编号不是列表格式: {url_num_list_json}")

        if not valuable_results_data:
            logger.warning("未能从LLM响应中提取到有价值的URL结果。")
            return SearchResults(search_request=search_request)
        logger.debug(f"有价值的搜索结果: {valuable_results_data}")
        if valuable_results_data:
            search_plan_result = deepscan(
                search_response=valuable_results_data, search_request=search_request
            )
            return search_plan_result
        else:
            logger.warning("没有找到有价值的搜索结果。")
            return SearchResults(search_request=search_request)
    except Exception as e:
        logger.error(f"执行搜索计划时出错: {str(e)}")
        return SearchResults(search_request=search_request)

def deepresearch_tool(messages: list[dict]):
    executed_search_plans = []
    max_plan_iterations = 12
    accumulated_search_results = SearchResults()
    yield "🔍 **开始深度研究搜索...**\n\n"

    # 执行初始搜索获取参考信息
    yield "📋 **初始搜索获取参考信息**\n"
    search_reference_results = search_core(messages=str(messages), deep=False)
    yield "✅ 初始搜索完成\n\n"

    # 生成第一个搜索计划
    yield "📌 **生成第一个搜索计划**\n"
    current_search_plan_steps = generate_search_plan(
        messages=messages,
        web_reference=search_reference_results.to_str() if search_reference_results else ""
    )
    
    if not current_search_plan_steps:
        yield "⚠️ 第一个搜索计划未能生成。\n\n"
        yield "🏁 **深度研究结束**\n\n"
        yield f"results{accumulated_search_results.to_str()}"
        return

    # 显示第一个搜索计划
    executed_plan_item = current_search_plan_steps[0]
    yield from format_search_plan(executed_plan_item)
    
    # 执行第一个搜索计划
    yield "🔄 **执行第一个搜索计划**\n"
    current_results = _execute_search_plan(executed_plan_item)
    logger.debug(f"当前搜索结果: {current_results.to_str()}")
    yield from format_urls(current_results.get_urls())
    executed_search_plans.append(executed_plan_item)
    accumulated_search_results.merge(current_results)
    excluded_urls = accumulated_search_results.get_urls()
    yield "✅ 搜索计划1执行完成\n\n"

    plan_counter = 2
    
    # 继续生成和执行后续搜索计划
    try:
        while len(executed_search_plans) < max_plan_iterations:
            yield f"📊 **已执行的搜索计划数量：** {len(executed_search_plans)}/{max_plan_iterations}\n"
            # 生成下一个搜索计划
            yield f"📌 **步骤{plan_counter}：生成下一个搜索计划**\n"
            current_search_plan_steps = generate_search_plan(
                messages=messages,
                previous_plan=str([plan.get("search_purpose",'') for plan in executed_search_plans]),
                previous_results=accumulated_search_results.to_str(),
                max_remaining_steps=max_plan_iterations - len(executed_search_plans)
            )

            if not current_search_plan_steps or len(current_search_plan_steps) == 0:
                yield "🏁 **未能生成新的搜索计划，信息获取完毕，深度研究提前完成**\n\n"
                break

            # 显示搜索计划
            executed_plan_item = current_search_plan_steps[0]
            yield from format_search_plan(executed_plan_item)
            
            # 执行搜索计划
            yield f"🔄 **执行搜索计划{plan_counter}**\n"
            current_results = _execute_search_plan(executed_plan_item,excluded_urls=excluded_urls)
            yield from format_urls(current_results.get_urls())
            accumulated_search_results.merge(current_results)
            excluded_urls += accumulated_search_results.get_urls()
            executed_search_plans.append(executed_plan_item)
            yield f"✅ 搜索计划{plan_counter}执行完成\n\n"
            plan_counter += 1

        # 处理循环结束后的情况
        if len(executed_search_plans) >= max_plan_iterations:
            yield f"🏁 **已达到最大搜索计划数量({max_plan_iterations})，深度研究完成**\n\n"
        elif not executed_search_plans:
            yield "🏁 **未能执行任何搜索计划，深度研究结束**\n\n"
        else:
            yield "🏁 **深度研究完成**\n\n"

        yield "✅ **深度研究搜索完成**\n"
    except:
        traceback.print_exc()
        yield "🚫 **研究过程出现意外,强行终止**"
    
    # 将结果写入文件
    try:
        with open("temp_research.txt", "w", encoding="utf-8") as fp:
            fp.write(accumulated_search_results.to_str())
        yield f"💾 结果已保存到 temp_research.txt\n"
    except IOError as e:
        logger.error(f"写入 temp_research.txt 文件失败: {e}")
        yield f"⚠️ 无法写入结果文件: {e}\n"

    yield f"results{accumulated_search_results.to_str()}"



if __name__ == "__main__":
    user_messages_example = [{"role": "user", "content": "介绍一下chatgpt o4mini"}]
    # print(f"正在对 \"{user_messages_example[0]['content']}\" 进行深度研究...")
    for item in deepresearch_tool(user_messages_example):
        logger.info(item)
    logger.info("--- 研究结束 ---")
