import sys
import json
from pathlib import Path

from openai import OpenAI

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from config.base_config import SEARCH_KEYWORD_MODEL, SEARCH_KEYWORD_API_KEY, SEARCH_KEYWORD_API_URL
from config.logging_config import logger
from app.utils.tools import response2json, get_time, json2SearchRequests, format_search_plan
from app.utils.prompt import SEARCH_PROMPT
from app.search.search_after_ai import search_ai

def search_core(messages: str, deep: bool = True):
    messages = [{'role': 'user', 'content': SEARCH_PROMPT.substitute(messages=messages,current_time=get_time())}] 
    client = OpenAI(
        api_key=SEARCH_KEYWORD_API_KEY,
        base_url=SEARCH_KEYWORD_API_URL
    )
    llm_rsp = client.chat.completions.create(
        model=SEARCH_KEYWORD_MODEL,
        messages=messages,
        temperature=0.1,
        stream=False
    )
    results = response2json(llm_rsp.choices[0].message.content)
    # print(f"搜索关键词生成结果: {json.dumps(results,indent=4,ensure_ascii=False)}")

    if results is None:
        logger.error("!!!搜索关键词生成失败!!!")
        return  ""
    else:
        search_request = json2SearchRequests(results)
        search_results = search_ai(search_request=search_request, deep=deep)
        return search_results

def search_tool(messages: str):
    messages = [{'role': 'user', 'content': SEARCH_PROMPT.substitute(messages=messages, current_time=get_time())}]
    logger.info("调用普通搜索工具")
    client = OpenAI(
        api_key=SEARCH_KEYWORD_API_KEY,
        base_url=SEARCH_KEYWORD_API_URL
    )
    
    llm_rsp = client.chat.completions.create(
        model=SEARCH_KEYWORD_MODEL,
        messages=messages,
        temperature=0.1,
        stream=False
    )
    
    results = response2json(llm_rsp.choices[0].message.content)
    logger.info(
        "🔍 搜索关键词生成结果：\n```json\n%s\n```\n",
        json.dumps(results, indent=4, ensure_ascii=False),
    )
    
    if results is None:
        yield "❌ **搜索关键词生成失败！**"
        return " "
    
    search_request = json2SearchRequests(results)
    yield from format_search_plan(results)
    yield "\n🔎 开始执行搜索，请稍候...\n"

    search_results = search_ai(search_request=search_request, deep=True).to_str()

    yield "✅ **搜索完成**\n"
    yield f"results{search_results}"



if __name__ == "__main__":
    messages = [{'role': 'user', 'content': '帮我搜一下最近openai新发布的那个模型的信息'}]
    search_results = search_tool(str(messages))
    for i in search_results:
        logger.info(i)
