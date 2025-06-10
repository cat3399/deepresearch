"""
工具模块，提供JSON解析、SSE数据转换、搜索请求处理等功能。
"""

import ast
import json
import re
import sys
import time
import traceback
import logging
from pathlib import Path
from typing import Dict, List, Union

from bs4 import BeautifulSoup
import docx
import fitz
from openai import OpenAI
import openpyxl
from pydocx import PyDocX
import requests
import xlrd

# 添加根目录到系统路径
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from app.search.models import SearchRequest,QueryKeys
from app.utils.config import AVAILABLE_EXTENSIONS

def response2json(text: str, mode: str = "json_str") -> Union[Dict, List, None]:
    """
    从字符串中提取第一个 { 和最后一个 } 之间的内容 或者 第一个 [ 和 最后一个 ] 之间的内容,
    并尝试将其解析为 JSON 对象或列表。
    会根据 mode 优先尝试解析。如果首选类型未找到，会尝试另一种类型作为回退。

    参数:
        text (str): 要处理的输入字符串
        mode (str): "json_str" (默认) 优先查找 JSON 对象 ({...}),
                    "json_list" 优先查找 JSON 列表 ([...])。

    返回:
        dict/list/None: 成功时返回解析后的 JSON 对象或列表, 失败时返回 None
    """
    if text.rstrip(" ").startswith("<think>"):
        text = text.split("</think>",maxsplit=1)[-1]
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    
    pattern_json_obj = r"({.*})"  # 匹配 JSON 对象: 第一个 { 到最后一个 }
    pattern_json_list = r"(\[.*\])"  # 匹配 JSON 列表: 第一个 [ 到最后一个 ]
    
    match_obj = re.search(pattern_json_obj, text, re.DOTALL)
    match_list = re.search(pattern_json_list, text, re.DOTALL)
    
    string_to_parse = None
    
    if mode == "json_list":
        if match_list:
            string_to_parse = match_list.group(1)
        elif match_obj:  # 回退: 如果列表模式下未找到列表，则尝试对象
            string_to_parse = match_obj.group(1)
    else:
        if match_obj:
            string_to_parse = match_obj.group(1)
        elif match_list:  # 回退: 如果对象模式下未找到对象，则尝试列表
            string_to_parse = match_list.group(1)
    
    if string_to_parse:
        try:
            parsed_json_content = json.loads(string_to_parse)
            return parsed_json_content
        except json.JSONDecodeError as e:
            logging.error(f"JSON 解析失败: {e}")
            return None
    else:
        logging.warning("未找到匹配的 JSON 格式内容")
        return None


def response2list(llm_output: str) -> list[int]:
    """
    从任意LLM输出中提取整数列表
    
    Args:
        llm_output (str): 大模型的输出文本
        
    Returns:
        list: 提取出的整数列表，如果没有找到则返回空列表
    """
    # 正则表达式匹配列表格式
    llm_output = str(llm_output)
    list_pattern = r'\[\s*(?:\d+\s*(?:,\s*\d+\s*)*)?]'
    potential_lists = re.findall(list_pattern, llm_output)
    
    valid_lists = []
    for list_str in potential_lists:
        try:
            # 使用ast.literal_eval安全地解析列表
            parsed_list = ast.literal_eval(list_str)
            # 确保它是一个列表并且所有元素都是整数
            if isinstance(parsed_list, list) and all(isinstance(item, int) for item in parsed_list):
                valid_lists.append((list_str, parsed_list))
        except (SyntaxError, ValueError):
            continue
    
    if not valid_lists:
        return []
    
    # 如果只找到一个有效列表，直接返回
    if len(valid_lists) == 1:
        return valid_lists[0][1]
    
    # 如果有多个列表，优先选择最长的列表
    max_length = max(len(parsed_list) for _, parsed_list in valid_lists)
    longest_lists = [(list_str, parsed_list) for list_str, parsed_list in valid_lists 
                     if len(parsed_list) == max_length]
    
    # 如果有多个相同长度的列表，选择最后出现的那个
    last_list = None
    last_position = -1
    
    for list_str, parsed_list in longest_lists:
        list_pos = llm_output.rfind(list_str)
        if list_pos > last_position:
            last_position = list_pos
            last_list = parsed_list
    
    return last_list if last_list is not None else []


def get_time() -> str:
    """获取当前时间的格式化字符串"""
    return str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))


def sse_create_openai_data(content: str = '', reasoning_content: str = '') -> str:
    """创建OpenAI格式的SSE数据"""
    data_structure = {
        "choices": [
            {
                "delta": {
                    "content": str(content),
                    "reasoning_content": str(reasoning_content),
                    "role": "assistant"
                },
                "index": 0
            }
        ],
        "created": 0,  # 或者 int(time.time())
        "id": int(time.time()),
        "model": "summary_model",
        "service_tier": "default",
        "object": "chat.completion.chunk",
        "usage": None
    }
    json_data = json.dumps(data_structure, ensure_ascii=False)
    return f"data: {json_data}\n\n"


def sse_create_openai_usage_data(usage: dict) -> str:
    """创建OpenAI格式的使用统计SSE数据"""
    completion_tokens = usage.get("completion_tokens", 0)
    prompt_tokens = usage.get("prompt_tokens", 0)
    total_tokens = usage.get("total_tokens", 0)
    template = f"""data: {{"usage":{{"completion_tokens":{completion_tokens},"prompt_tokens":{prompt_tokens},"total_tokens":{total_tokens}}},"choices":[],"created":{time.time()},"id":"search-{time.time()}","model":"search-model","object":"chat.completion.chunk"}}\n\n"""
    return template


def sse_gemini2openai_data(gemini_sse_data: str) -> str:
    """将Gemini的SSE数据转换为OpenAI格式"""
    gemini_sse_data = gemini_sse_data.decode("utf-8")
    if gemini_sse_data.startswith("data: "):
        json_str = gemini_sse_data[6:]
        try:
            json_data = json.loads(json_str)
            content = json_data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
            data_structure = {
                "choices": [
                    {
                        "delta": {
                            "content": content,
                            "role": "assistant"
                        },
                        "index": 0
                    }
                ],
                "created": 0,
                "id": int(time.time()),
                "model": "summary_model", 
                "service_tier": "default",
                "object": "chat.completion.chunk",
                "usage": None
            }
            json_data = json.dumps(data_structure, ensure_ascii=False)
            return f"data: {json_data}\n\n"
        except Exception:
            pass
    else:
        logging.debug(gemini_sse_data)


def text2fc(llm_str: str) -> list:
    """从LLM输出中提取函数调用信息"""
    class fc:
        def __init__(self, name, arguments):
            self.function = self.function_llm(name, arguments)
            
        class function_llm:
            def __init__(self, name, arguments):
                self.name = name
                self.arguments = arguments
                
    pattern = r"<function_call>(.*?)</function_call>"
    matches = re.findall(pattern, llm_str, re.DOTALL)
    if matches:
        fc_text = matches[0].strip("\n")
        try:
            fc_json = json.loads(fc_text)
            fc_name = fc_json.get('name', None)
            fc_arguments = fc_json.get('arguments', None)
            fc_message = fc(fc_name, fc_arguments)
            return [fc_message]
        except Exception as e:
            logging.error("function call提取出问题")
            logging.error(e)
            logging.error(fc_text)


def json2SearchRequests(data: dict) -> SearchRequest:
    """
    将JSON数据转换为SearchRequest对象列表
    
    参数:
        data (dict): 包含搜索请求信息的字典，应包含'search_purpose'、'data'和'time_page'字段
        
    返回:
        list[SearchRequest]: SearchRequest对象列表
    """
    search_purpose = data.get('search_purpose', '')
    search_restrictions = data.get('search_restrictions','')
    search_data = data.get('data', [])
    time_page = data.get('time_page', '')
    # 验证search_data是列表
    if not isinstance(search_data, list):
        return []
    
    search_request = SearchRequest(
            query_keys=[QueryKeys(key=r.get('keys', ''),language=r.get('language', 'zh_CN')) for r in search_data],
            time_page=time_page,
            search_purpose=search_purpose,
            search_restrictions=search_restrictions
        )
    
    return search_request


def format_search_plan(plan_info: dict):
    """
    美化搜索计划输出的生成器函数 - 二级菜单样式
    """
    search_purpose = plan_info.get('search_purpose', '未知')
    search_restrictions = plan_info.get('search_restrictions', '无')
    search_keywords = [item.get('keys', '') for item in plan_info.get('data', [])]
    
    yield f"🎯 **搜索预期：** {search_purpose}\n"
    yield f"⭕ **结果限制：** {search_restrictions}\n"
    yield f"🔍 **搜索关键词：**\n"
    
    for keyword in search_keywords:
        yield f"\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0➤ {keyword}\n"

def format_urls(urls: List[str]):
    """
    美化URL列表输出的生成器函数
    """
    if not urls:
        yield "📝 **未查看任何网页内容**\n"
        return
    
    yield f"🌐 **已查看 {len(urls)} 个网页：**\n"
    
    for i, url in enumerate(urls, 1):
        if url:
            display_url = url if len(url) <= 100 else url[:120] + "..."
            yield f"\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0{i}. {display_url}\n"
    
    yield "\n"

DOWNLOAD_FILE_PATH = ROOT_DIR / "tmp_files"
def download_file(url):
    """
    从指定 URL 下载文件，并保存到 DOWNLOAD_FILE_PATH 目录。
    如果目录不存在，则创建该目录。
    
    Returns:
        Path|str: 成功时返回文件路径(Path对象，布尔值为True)，失败时返回空字符串(布尔值为False)
    """
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    DOWNLOAD_FILE_PATH.mkdir(parents=True, exist_ok=True)
    
    # 检查文件扩展名
    file_name = url.split('/')[-1]
    file_extension = Path(file_name).suffix.lower()
    if file_extension not in AVAILABLE_EXTENSIONS:
        return ''
    
    file_path = DOWNLOAD_FILE_PATH / file_name
    
    try:
        # 先发送HEAD请求检查文件大小（如果服务器支持）
        head_response = requests.head(url, timeout=10)
        if head_response.status_code == 200:
            content_length = head_response.headers.get('Content-Length')
            if content_length and int(content_length) > MAX_FILE_SIZE:
                logging.warning(
                    f"文件过大: {int(content_length) / (1024*1024):.1f}MB > 10MB"
                )
                return ''
        
        # 流式下载并限制大小
        response = requests.get(url, timeout=30, stream=True)
        response.raise_for_status()
        
        downloaded_size = 0
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    downloaded_size += len(chunk)
                    if downloaded_size > MAX_FILE_SIZE:
                        logging.warning(
                            f"下载过程中发现文件过大: {downloaded_size / (1024*1024):.1f}MB > 10MB"
                        )
                        # 删除部分下载的文件
                        file_path.unlink(missing_ok=True)
                        return ''
                    f.write(chunk)
        
        return file_path  # Path对象，布尔值为True
        
    except requests.RequestException as e:
        # 确保清理可能的部分文件
        if file_path.exists():
            file_path.unlink(missing_ok=True)
        return ''  # 空字符串，布尔值为False
    except Exception as e:
        # 确保清理可能的部分文件  
        if file_path.exists():
            file_path.unlink(missing_ok=True)
        return ''

def extract_text_from_file(file_path):
    """
    根据文件类型，从文件中提取纯文本内容。
    支持的格式: .pdf, .docx, .doc, .xlsx, .xls
    Args:
        file_path (str|Path): 文件路径，可以是字符串或Path对象
    Returns:
        str: 提取的文本内容，如果文件类型不支持或发生错误则返回错误信息
    """
    # 转换为 Path 对象以确保一致性
    file_path = Path(file_path)
    extension = file_path.suffix.lower()
    
    try:
        if extension == '.pdf':
            doc = fitz.open(file_path)
            text = "".join(page.get_text() for page in doc)
            doc.close()
            return text

        elif extension == '.docx':
            doc = docx.Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])

        elif extension == '.doc':
            html = PyDocX.to_html(str(file_path))  # PyDocX 可能需要字符串路径
            soup = BeautifulSoup(html, 'html.parser')
            return soup.get_text()

        elif extension == '.xlsx':
            text_parts = []
            workbook = openpyxl.load_workbook(file_path)
            for sheet in workbook.worksheets:
                for row in sheet.iter_rows():
                    for cell in row:
                        if cell.value:
                            text_parts.append(str(cell.value))
            return "\n".join(text_parts)

        elif extension == '.xls':
            text_parts = []
            workbook = xlrd.open_workbook(str(file_path))  # xlrd 可能需要字符串路径
            for sheet in workbook.sheets():
                for row_idx in range(sheet.nrows):
                    for col_idx in range(sheet.ncols):
                        cell_value = sheet.cell_value(row_idx, col_idx)
                        if cell_value:
                            text_parts.append(str(cell_value))
            return "\n".join(text_parts)
            
        else:
            return f"不支持的文件类型: {extension}"

    except Exception as e:
        logging.error(f"处理文件 {file_path.name} 时出错: {e}")
        return f"处理文件 {file_path} 时出错"
# ...existing code...

def chat_chat_completion():
    """
    对openai库的再封装,便于项目使用
    """
    pass


if __name__ == "__main__":
    t = '''
    {
        "search_purpose": "搜索在Linux环境下，特别是在Debian系统上，如何在RK3399平台使用QEMU的KVM加速功能。预期得到的内容包括：具体的配置步骤、安装和设置KVM加速的教程、可能需要的额外驱动或工具、针对RK3399硬件平台的特殊注意事项或限制、以及用户在实际操作中可能遇到的常见问题和解决方案。目标是为用户提供详细且可操作的指导，确保他们能够在Debian系统上成功启用QEMU的KVM加速。",
        "time_page": [0, 0, 0],
        "data": [
            {
                "keys": "RK3399 QEMU KVM acceleration Linux Debian",
                "language": "en-US"
            },
            {
                "keys": "How to enable KVM on QEMU for RK3399 in Debian",
                "language": "en-US"
            },
            {
                "keys": "RK3399 QEMU KVM setup guide Debian Linux",
                "language": "en-US"
            }
        ]
    }
    '''
    logging.info(json2SearchRequests(json.loads(t)))
    # usage = {"completion_tokens": 16, "prompt_tokens": 4, "total_tokens": 20}
    # print(sse_create_openai_usage_data(usage))
