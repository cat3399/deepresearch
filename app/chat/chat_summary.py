import json
import random
from openai import OpenAI
import time
from pathlib import Path
import sys
import logging

import requests

# 将项目根目录添加到sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from app.utils.tools import sse_create_openai_data, sse_gemini2openai_data
from app.utils.config import SUMMARY_API_KEY,SUMMARY_API_URL,SUMMARY_MODEL,SUMMARY_API_TYPE

if SUMMARY_API_TYPE != "GEMINI":
    client = OpenAI(
        api_key = SUMMARY_API_KEY,
        base_url = SUMMARY_API_URL,
    )
MAX_RETRIES = 3
SUMMARY_API_KEYS = SUMMARY_API_KEY.split(",")
def openai_stream_no(messages:list[dict], model:str = SUMMARY_MODEL):
    retry_count = 0
    while retry_count < MAX_RETRIES:
        try:
            start_time = time.time()
            # print(messages)
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.1
            )
            response_data = completion.choices[0].message.content
            # print(completion)
            processing_time = time.time() - start_time
            # print(completion)
            reason_content = completion.choices[0].message.reasoning_content
            messages.append({"role": "assistant", "content": response_data})
            logging.info(f"token消耗: {completion.usage.total_tokens}")
            logging.info(f"{model}处理耗时: {processing_time:.2f}秒")
            logging.info(
                f"{model}处理速度: {completion.usage.completion_tokens / processing_time:.2f}token/秒"
            )
            return response_data,reason_content

        except Exception as e:
            retry_count += 1
            if retry_count >= MAX_RETRIES:
                logging.error(f"json_data: {completion.model_dump_json()}")
                logging.error(f"{model}请求失败: {str(e)}")
                return "请求失败"
            else:
                logging.warning(f"{model}请求失败: {str(e)} 正在重试{retry_count}")

def openai_stream_yes(messages: list[dict], model: str = SUMMARY_MODEL):
    retry_count = 0
    while retry_count < MAX_RETRIES:
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                # temperature=0.1,
                stream_options={"include_usage": True}
            )
            for chunk in completion:
                try:
                    chunk_reasoning_content = chunk.choices[0].delta.reasoning_content
                    # print(chunk_reasoning_content)
                    if chunk_reasoning_content is not None:
                        yield sse_create_openai_data(reasoning_content=chunk_reasoning_content)
                except:
                    pass
                try:
                    chunk_content = chunk.choices[0].delta.content
                    # print(chunk_content)
                    if chunk_content is not None:
                        yield sse_create_openai_data(content=chunk_content)
                except:
                    pass
            try:
                logging.info("总结模型花费token: %s", chunk.usage.total_tokens)
            except Exception:
                pass
            
            return 

        except Exception as e:
            retry_count += 1
            if retry_count >= MAX_RETRIES:
                logging.error(f"{model}请求失败: {str(e)}")
                yield "请求失败"
                return
            else:
                logging.warning(f"{model}请求失败: {str(e)} 正在重试{retry_count}")

def gemini_stream_no(messages: list[str],model:str = SUMMARY_MODEL) -> str:
    retry_count = 0
    while retry_count < MAX_RETRIES:
        try:
            start_time = time.time()
            api_key = random.choice(SUMMARY_API_KEY)
            # print(messages)
            # Gemini API URL
            api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

            messages_tmp = [{**msg,'role':'model'} if msg['role'] == "assistant" else msg for msg in messages]
            for msg in messages_tmp:
                msg['parts']=[{"text": msg['content']}]
                msg.pop('content')
            if messages_tmp[0]['role'] == "system":
                messages_tmp = messages_tmp[1::]
            payload = {
                'contents': messages_tmp
                        }
            # 设置请求头
            headers = {
                "Content-Type": "application/json"
            }

            payload = {
                "contents": messages_tmp,
                "generationConfig": {
                    # "maxOutputTokens": 8192,
                    "temperature": 0.1
                }
            }  
            # print(json.dumps(payload))
            res = requests.post(url=api_url,headers=headers,data=json.dumps(payload))
            res_data = res.json()
            try:
                cost_chat_token = res_data['usageMetadata']['candidatesTokenCount']
                cost_totle_token = res_data['usageMetadata']['totalTokenCount']
                cost_time = time.time() - start_time
                speed = f"{model}处理速度 {cost_chat_token/cost_time:.2f} token/s"
                logging.info(f"{model}总共花费{cost_totle_token} token")
                logging.info(speed)
            except Exception as e:
                logging.debug(res_data['usageMetadata'])
                logging.error(f"获取token输出速度失败 {e}")
            return res_data['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            retry_count += 1
            logging.debug(res_data)
            logging.debug(res)
            if retry_count >= MAX_RETRIES:
                logging.error(f"gemini回复出现问题!!! {e}\n 正在重试{retry_count}")
                return 'error'
            else:
                logging.warning(f"gemini回复出现问题!!! {e}\n 正在重试{retry_count}")

def gemini_stream_yes(messages: list[str],model:str = SUMMARY_MODEL):
    retry_count = 0
    try:
        api_key = random.choice(SUMMARY_API_KEYS)
        logging.debug("SUMMARY_API_KEY", SUMMARY_API_KEYS)
        logging.debug("使用的GEMINI KEY", api_key)
        # print(messages)
        # Gemini API URL
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?alt=sse&key={api_key}"

        messages_tmp = [{**msg,'role':'model'} if msg['role'] == "assistant" else msg for msg in messages]
        for msg in messages_tmp:
            msg['parts']=[{"text": msg['content']}]
            msg.pop('content')
        if messages_tmp[0]['role'] == "system":
            messages_tmp = messages_tmp[1::]
        payload = {
            'contents': messages_tmp
                    }
        # 设置请求头
        headers = {
            "Content-Type": "application/json"
        }

        payload = {
            "contents": messages_tmp,
            "generationConfig": {
                # "maxOutputTokens": 8192,
                "temperature": 0.1
            }
        }  
        # print(json.dumps(payload))
        res = requests.post(url=api_url,headers=headers,data=json.dumps(payload),stream=True)
        return res

    except Exception as e:
        retry_count += 1
        logging.debug(res)
        if retry_count >= MAX_RETRIES:
            logging.error(f"gemini回复出现问题!!! {e}\n 正在重试{retry_count}")
            return sse_create_openai_data(content=f'Gemini出现问题{e}')
        else:
            logging.warning(f"gemini回复出现问题!!! {e}\n 正在重试{retry_count}")

def summary(messages:list[dict], model:str = SUMMARY_MODEL, stream:bool =False):
    """
    与deepseek API 进行文字对话 (非流式)。

    Args:
        model: 要使用的模型名称 (例如 "qwen-max-lastest")
        messages: 一个消息列表,每个消息是一个字典,包含 "role" (user 或 assistant) 和 "content"
        stream: 是否使用流式传输
    Returns:
        模型回复的文本内容
    """

    with open("summary.txt",'w') as fp:
        fp.write(str(messages))
    
    if SUMMARY_API_TYPE == "GEMINI":
        if stream:
            rsp_stream = gemini_stream_yes(messages,model)
            for line in rsp_stream.iter_lines():
                if line:
                    # print(line)
                    yield sse_gemini2openai_data(line)
        else:
            return gemini_stream_no(messages,model)
    else:
        if stream:
            yield from openai_stream_yes(messages,model)
        else:
            return openai_stream_no(messages,model)

# 使用示例
if __name__ == "__main__":
    user_messages = [
        {"role": "user", "content": "你好,简短的介绍一下你自己吧"},
    ]

    # response_data,reason_content = chat_with_deepseek(user_messages)

    # print("r1:", reason_content,response_data)

    s = summary(messages=user_messages,model=SUMMARY_MODEL,stream=True)
    # time.sleep(5)
    for ss in s:
        if ss:
            logging.info(ss)
