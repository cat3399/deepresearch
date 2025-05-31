import logging
from pathlib import Path
import sys
import time
import random
import requests
import json
import os

# 将项目根目录添加到sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from app.utils.tools import sse_create_openai_data, sse_gemini2openai_data
from app.utils.config import COMPRESS_API_KEY

API_KEYS = COMPRESS_API_KEY.split(",")
print(f"gemini使用的API密钥: {API_KEYS}")

MODEL = "gemini-2.5-pro-exp-03-25"
# MODEL = "gemini-2.0-flash-thinking-exp-01-21"
# MODEL = "gemini-2.0-flash"

def stream_no(messages: list[str],model:str = MODEL) -> str:
    retry_count = 0
    while retry_count < MAX_RETRIES:
        try:
            start_time = time.time()
            api_key = random.choice(API_KEYS)
            # print(messages)
            # Gemini API URL
            api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={api_key}"

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
                print(f"{model}总共花费{cost_totle_token} token")
                print(speed)
            except Exception as e:
                print(res_data['usageMetadata'])
                print(f"获取token输出速度失败 {e}")
            return res_data['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            retry_count += 1
            print(res_data)
            print(res)
            if retry_count >= MAX_RETRIES:
                print(f"gemini回复出现问题!!! {e}\n 正在重试{retry_count}")
                return 'error'
            else:
                print(f"gemini回复出现问题!!! {e}\n 正在重试{retry_count}")

def stream_yes(messages: list[str],model:str = MODEL):
    retry_count = 0
    try:
        start_time = time.time()
        api_key = random.choice(API_KEYS)
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
        # for line in res.iter_lines():
        #     decoded_line = line.decode('utf-8')
        #     if decoded_line.startswith("data:"):
        #         # print(decoded_line[6:])
        #         line_json = json.loads(decoded_line[6:])
        #         llm_content = line_json.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
        #         # llm_content = line_json.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
        #         print(llm_content,end='')
                # if 
                # pass
            # print(decoded_line)
        # try:
        #     cost_chat_token = res_data['usageMetadata']['candidatesTokenCount']
        #     cost_totle_token = res_data['usageMetadata']['totalTokenCount']
        #     cost_time = time.time() - start_time
        #     speed = f"{model}处理速度 {cost_chat_token/cost_time:.2f} token/s"
        #     print(f"{model}总共花费{cost_totle_token} token")
        #     print(speed)
        # except Exception as e:
        #     print(res_data['usageMetadata'])
        #     print(f"获取token输出速度失败 {e}")
        # return res_data['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        retry_count += 1
        print(res)
        if retry_count >= MAX_RETRIES:
            print(f"gemini回复出现问题!!! {e}\n 正在重试{retry_count}")
            return sse_create_openai_data(content=f'Gemini出现问题{e}')
        else:
            print(f"gemini回复出现问题!!! {e}\n 正在重试{retry_count}")

MAX_RETRIES=3
def chat_with_gemini(messages: list[str],model:str = MODEL, stream:bool =False):
    if stream:
        rsp_stream = stream_yes(messages=messages,model=model)
        for line in rsp_stream.iter_lines():
            if line:
                print(line.decode("utf-8"))
                # print(sse_gemini2openai_data(line))
                yield sse_gemini2openai_data(line)
        # return stream_yes(messages=messages,model=model)
    else:
        return stream_no(messages=messages,model=model)


if __name__ == "__main__":
    user_input = r"""
    你好
"""
    messages = [
    {'role': 'user', 'content': user_input},
    ]
    STREAM_MODE = True
    MODEL1 = "gemini-2.0-flash"


    rsp = chat_with_gemini(messages,model=MODEL1,stream=STREAM_MODE)
    if STREAM_MODE:
        for line in rsp:
            print(line)
    else:
        print(rsp)