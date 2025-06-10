import json
from pathlib import Path
import sys
import time
import ast
import logging
from typing import Dict, Any, Callable
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor

# 将项目根目录添加到sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from app.utils.tools import sse_create_openai_data, response2json, get_time
from app.utils.url2txt import url_to_markdown
from app.utils.config import BASE_CHAT_API_KEY, BASE_CHAT_API_URL, BASE_CHAT_MODEL
from app.utils.prompt import DATA_ADD_PROMPT
from app.search.search_after_ai import search_ai
from app.search.fc_search import search_tool
from app.search.fc_deepresearch import deepresearch_tool
from app.chat.chat_summary import summary

# 创建客户端
CLIENT = OpenAI(
    api_key=BASE_CHAT_API_KEY,
    base_url=BASE_CHAT_API_URL
)

class FunctionRegistry:
    def __init__(self):
        self.functions: Dict[str, Callable] = {}
        self.tools = []
    
    def register(self, description: Dict[str, Any]):
        """装饰器: 注册函数和其描述"""
        def decorator(func: Callable):
            name = func.__name__
            self.functions[name] = func
            self.tools.append({
                'type': 'function',
                'function': {
                    'name': name,
                    **description
                }
            })
            return func
        return decorator

    def call(self, name: str, arguments: str) -> Any:
        """调用已注册的函数"""
        if name not in self.functions:
            raise ValueError(f"Function {name} not found")
        args = json.loads(arguments)
        return self.functions[name](**args)

registry = FunctionRegistry()

@registry.register({
    'description': '联网搜索工具,能够根据用户需求搜索时效性信息,不需要任何参数,直接调用即可',
    'parameters': {
        'type': 'object',
        'properties': {}}})(search_tool)


# @registry.register({
#     'description': '网页内容获取工具,能够根据url获取网页的markdown格式内容,支持一次性单个和多个url传入',
#     'parameters': {
#         'type': 'object',
#         'properties': {
#             'urls': {
#                 'type': 'array',
#                 'items':{
#                     'type': 'string',
#                 },
#                 'description': '网页url',
#             },
#         "required": ["urls"]
#     }
# }})
def get_url_content(urls: list[str]) -> str:
    content_dict = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_results = executor.map(url_to_markdown,urls)
        content_dict = dict(zip(urls,future_results))

    # result = url_to_markdown(url)
    # if result == 'error':
    #     return '获取网页内容失败'
    return str(content_dict)

def chat_completion(messages: list, chat_model=BASE_CHAT_MODEL, client=CLIENT, use_tools=False, stream :bool = False) -> Any:
    start_time = time.time()
    
    # 记录请求数据
    request_data = {
        "model": chat_model,
        "messages": messages,
        "temperature": 0.1,
        "stream": stream,
        # 'stream_options':
        #     {"include_usage": True}
    }
    if use_tools:
        request_data["tools"] = registry.tools
        response = client.chat.completions.create(**request_data)
    else:
        response = client.chat.completions.create(**request_data)
    
    if not stream:
        # 打印响应信息
        processing_time = time.time() - start_time
        logging.info(f"token消耗: {response.usage.total_tokens}")
        logging.info(f"处理时间: {processing_time} s")
        logging.info(
            f"处理速度: {int(response.usage.completion_tokens/processing_time)} token/s"
        )
        return response.choices[0].message
    else:
        return response

def process_messages_stream(messages: list, search_mode: int = 1):
    # 添加系统提示(如果有)
    # messages = [{'role': 'system', 'content': SYS_PROMPT}] + messages
    assistant_rsp = chat_completion(messages, use_tools=True, stream=True)
    content_result = ' '
    tool_calls = None
    # print(assistant_rsp)
    for chunk in assistant_rsp:
        delta = chunk.choices[0].delta
        # print(delta)
        try:
            if delta.reasoning_content is not None:
                yield sse_create_openai_data(reasoning_content=delta.reasoning_content)
        except Exception:
            pass

        try:
            if delta.content and delta.tool_calls is None:
                content_result += delta.content
                yield sse_create_openai_data(reasoning_content=delta.content)
        except Exception:
            pass 

        try:
            if tool_calls is None:
                tool_calls = delta.tool_calls
            else:
                tool_calls[0].function.arguments += delta.tool_calls[0].function.arguments
        except Exception:
            pass

    yield sse_create_openai_data(reasoning_content="\n\n")
    if tool_calls:
        logging.debug(tool_calls)
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = tool_call.function.arguments
            if function_name == 'search_tool':
                if messages[0]['role'] == 'system':
                    messages = messages[1:]
                search_result = ""
                if search_mode == 2:
                    function_output = deepresearch_tool(str(messages))
                else:
                    function_output = search_tool(str(messages))
                for line in function_output:
                    if line.startswith("results"):
                        search_result = str(line[7:])
                        messages[-1]['content'] = messages[-1]['content'] + DATA_ADD_PROMPT.substitute(current_time=get_time(),search_result=search_result)
                    elif line:
                        yield sse_create_openai_data(reasoning_content=line)
                rsp_stream = summary(messages, stream=True)
                for line in rsp_stream:
                    yield line
                # yield sse_create_openai_data(content=search_result)

            if function_name == 'get_url_content':
                json_args = json.loads(function_args)
                for url in json_args['urls']:
                    yield sse_create_openai_data(reasoning_content=f"我正在获取 {url} 网页的内容\n")
                yield sse_create_openai_data(reasoning_content=' ')
                function_output = registry.call(function_name, function_args)
                messages[-1]['content'] = messages[-1]['content'] + f"现在的时间是{get_time()} 这是网页的内容 \n {function_output[:40000:]}"

                # rsp_stream = summary(messages,stream=True)
                # for line in rsp_stream:
                #     yield line
                #     yield sse_create_openai_data('')
                yield from summary(messages,stream=True)


    else:
        # assistant_message = {'role': 'assistant', 'content': assistant_rsp.content}
        # messages.append(assistant_message)
        yield sse_create_openai_data(content=content_result)

def process_messages(messages: list, stream: bool = False, search_mode: int = 1):
    logging.info("非流模式")
    assistant_reply = chat_completion(messages, use_tools=False)
    logging.info(assistant_reply)
    # 未完善,非流暂时只支持简单对话,用于测试
    # tool_calls = getattr(assistant_reply, 'tool_calls', None)
    # if tool_calls:
    #     print(tool_calls)
    #     for tool_call in tool_calls:
    #         function_name = tool_call.function.name
    #         function_args = tool_call.function.arguments
    #         function_output = registry.call(function_name, function_args)
    #         if function_name == 'search_tool':
    #             messages[-1]['content'] = messages[-1]['content'] + f"现在的时间是{get_time()} 这是一些网络搜索的的资料 请注意,这些资料均为网上收集获取的,并且不一定与主题相关,需要注意辨别真伪,忽略掉他人的总结类型信息,最好根据官方资料/权威资料（如果有）进行总结,如果用户问题需要时间控制,请分析资料的时间是否满足要求 \n{function_output}"
    #             gemini_response = summary(messages)
    #             assistant_message = {'role': 'assistant', 'content': gemini_response + ' by Gemini'}
    #             assistant_message['content'] = assistant_message['content']+ "\n" +function_output

    #         if function_name == 'get_url_content':
    #             messages[-1]['content'] = messages[-1]['content'] + f"这是网页的内容 \n {function_output[:40000:]}"
    #             deepseek_response, reason_response = summary(messages)
    #             assistant_message = {'role': 'assistant', 'content': f"<thinking>{reason_response}</thinking>" + deepseek_response + ' by DeepSeek'}
    #             assistant_message['content'] = assistant_message['content'] + "\n" +function_output
    #             assistant_message['reasoning_content'] = reason_response
    #         messages.append(assistant_message)

    # else:
    #     assistant_message = {'role': 'assistant', 'content': assistant_reply.content}
    #     messages.append(assistant_message)
    assistant_message = {'role': 'assistant', 'content': assistant_reply.content}

    return assistant_message