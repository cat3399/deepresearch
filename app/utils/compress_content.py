import sys
import time
import requests
import json
from pathlib import Path
from openai import OpenAI

# 将项目根目录添加到sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from app.utils.url2txt import url_to_markdown
from config import base_config as config
from config.logging_config import logger
from app.utils.prompt import SYSTEM_PROMPT_SUMMARY

"""
target_type 1: 
target_type 2: 
"""

def by_gemini(url: str, user_input: str, title: str = "",target_type:str = '1') -> str:
    """
    使用大模型对网页内容进行提取和处理,提高信息密度

    Args:
        url: 要处理的网页URL
        user_input: 用户输入的要求
        target_type: 处理类型,默认为'1'

    Returns:
        str: 生成的文本内容

    Raises:
        Exception: 当API调用或内容处理失败时
    """
    if not url:
        return ''
    try:
        logger.info(f"开始提取网页内容: {url}")
        start_time = time.time()
        
        # 使用默认配置或传入的配置
        if target_type == '1':
            SYSTEM_PROMPT = SYSTEM_PROMPT_SUMMARY
            
        # 抓取网页内容
        html_content = url_to_markdown(url)
        html_len = len(html_content)
        
        if html_len > 2000:            
            # 准备请求数据
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": f"用户需要的信息:{user_input}\n\n 网页的标题与摘要是{title} 网页的url是{url} 网页内容:{html_content[:70000:]}"
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    # "maxOutputTokens": 8192,
                    "temperature": 0.2
                },
                "systemInstruction": {
                    "parts": [
                        {
                            "text": SYSTEM_PROMPT
                        }
                    ]
                }
            }
            
            # 设置请求头
            headers = {
                "Content-Type": "application/json"
            }
            
            # 重试机制,最多重试3次,间隔1秒
            response_text = None
            response_json = None
            
            for attempt in range(3):
                try:
                    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{config.COMPRESS_MODEL}:generateContent?key={config.COMPRESS_API_KEY}"
                    # 发送POST请求
                    response = requests.post(api_url, headers=headers, data=json.dumps(payload),timeout=180) # 三分钟超时
                    response.raise_for_status()
                    
                    # 解析响应
                    response_json = response.json()
                    
                    # 从响应中提取文本
                    if "candidates" in response_json and len(response_json["candidates"]) > 0:
                        candidate = response_json["candidates"][0]
                        if "content" in candidate and "parts" in candidate["content"]:
                            parts = candidate["content"]["parts"]
                            if len(parts) > 0 and "text" in parts[0]:
                                response_text = parts[0]["text"]
                                break
                    
                    if not response_text:
                        logger.warning(
                            f"API响应未包含预期的文本内容: {response_json}"
                        )
                        time.sleep(1)
                        
                except Exception as e:
                    logger.error(
                        f"第 {attempt + 1} 次调用失败: {str(e)},1秒后重试..."
                    )
                    time.sleep(1)
                    
            if response_text is None:
                raise Exception("连续3次调用均失败")
            if response_text.rstrip().startswith("<think>"):
                    response_text = response_text.split("</think>",maxsplit=1)[-1]
            processing_time = time.time() - start_time
            
            try:
                # 获取token消耗信息
                logger.info(f"使用模型 {config.COMPRESS_MODEL}")
                if response_json and "usageMetadata" in response_json:
                    usage = response_json["usageMetadata"]
                    if "totalTokenCount" in usage:
                        logger.info(
                            f"gemini token消耗: {usage['totalTokenCount']}"
                        )
                logger.info(f"网页:{url}")
                logger.info(
                    f"gemini处理耗时: {processing_time:.2f}秒"
                )
                logger.info(
                    f"gemini处理速度: {len(response_text) / processing_time:.2f}字符/秒"
                )
                logger.info(f"原始内容长度{html_len}")
                logger.info(f"压缩后内容长度{len(response_text)}")
                logger.info(
                    f"压缩率{len(response_text)/html_len:.2f} \n"
                )
            except Exception as e:
                logger.error(f"处理速度计算失败: {str(e)}")
            if len(response_text) < 50 and "//--++" in response_text:
                # if '+' in response_text:
                #     return response_text[:40000:]
                if '-' in response_text:
                    return ''
            return response_text.strip()
        else:
            return html_content

    except Exception as e:
        logger.error(f"gemini处理失败: {str(e)}")
        return ''


def by_openai(url: str, user_input: str, title: str = "",target_type:str = '1'):
    """
    使用OpenAI对网页内容进行提取和处理,提高信息密度

    Args:
        url: 要处理的网页URL
        user_input: 用户输入的要求
        title: 网页标题
        target_type: 处理类型,默认为'1'

    Returns:
        str: 生成的文本内容
    """
    if not url:
        return ''
    
    try:
        logger.info(f"开始提取网页内容: {url}")
        start_time = time.time()
        
        # 使用默认配置或传入的配置
        if target_type == '1':
            SYSTEM_PROMPT = SYSTEM_PROMPT_SUMMARY
            
        # 抓取网页内容
        html_content = url_to_markdown(url)
        html_len = len(html_content)
        
        if html_len > 2000:
            # 准备消息
            messages = [
                {'role':'system','content':SYSTEM_PROMPT},
                {'role':'user','content':f"用户需要的信息:{user_input}\n\n 网页的标题与摘要是{title} 网页的url是{url} 网页内容:{html_content[:70000:]}"}
            ]
            
            client = OpenAI(api_key=config.COMPRESS_API_KEY,base_url=config.COMPRESS_API_URL)
            
            # 重试机制,最多重试3次,间隔1秒
            response_text = None
            completion = None
            
            for attempt in range(3):
                try:
                    completion = client.chat.completions.create(
                        model=config.COMPRESS_MODEL,
                        messages=messages,
                        temperature=0.1,
                    )
                    
                    response_text = completion.choices[0].message.content
                    if response_text:
                        break
                        
                except Exception as e:
                    logger.error(
                        f"第 {attempt + 1} 次调用失败: {str(e)},1秒后重试..."
                    )
                    time.sleep(1)
                    
            if response_text is None:
                raise Exception("连续3次调用均失败")
            if response_text.rstrip().startswith("<think>"):
                response_text = response_text.split("</think>",maxsplit=1)[-1]
            processing_time = time.time() - start_time
            
            try:
                # 获取token消耗信息
                if completion and completion.usage:
                    logger.info(f"{config.COMPRESS_MODEL} token消耗: {completion.usage.total_tokens}")
                logger.info(f"网页:{url}")
                logger.info(f"{config.COMPRESS_MODEL}处理耗时: {processing_time:.2f}秒")
                logger.info(f"{config.COMPRESS_MODEL}处理速度: {len(response_text) / processing_time:.2f}字符/秒")
                logger.info(f"原始内容长度{html_len}")
                logger.info(f"压缩后内容长度{len(response_text)}")
                logger.info(f"压缩率{len(response_text)/html_len:.2f} \n")
            except Exception as e:
                logger.error(f"处理速度计算失败: {str(e)}")
                
            if len(response_text) < 50 and "//--++" in response_text:
                if '-' in response_text:
                    return ''
                    
            return response_text.strip()
        else:
            return html_content
            
    except Exception as e:
        logger.error(f"{config.COMPRESS_MODEL}处理失败: {str(e)}")
        return ''


def compress_url_content(url: str, user_input: str, title: str = "",target_type:str = '1') -> str:
    """
    使用大模型对网页内容进行提取和处理,提高信息密度

    Args:
        url: 要处理的网页URL
        user_input: 用户输入的要求
        target_type: 处理类型,默认为'1'

    Returns:
        str: 生成的文本内容

    Raises:
        Exception: 当API调用或内容处理失败时
    """
    text = ""
    if config.COMPRESS_API_TYPE == "GEMINI":
        text = by_gemini(url,user_input,title,target_type)
    else:
        text = by_openai(url,user_input,title,target_type)
    return text

if __name__ == "__main__":
    # 示例用法
    test_url = r"https://tieba.baidu.com/home/main/?id=tb.1.83af9dd9.uDPZD2sU3nTxtBfZQQRcGQ"
    # test_url = r"https://help.aliyun.com/zh/model-studio/user-guide/vision/"
    # test_url = r"https://apps.apple.com/de/app/chatgpt/id6448311069"
    need_infomation = """
猫呀3399的发帖记录 活跃情况等
"""
#     need_infomation = """
# qwen大模型图片和视频相关api文档"""
#     need_infomation = """
# chatgpt plus的订阅价格"""
    result = compress_url_content(test_url, need_infomation, title="猫呀3399的贴吧")
    logger.info(result)
    