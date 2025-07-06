import sys
import time
import traceback
from pathlib import Path
from openai import OpenAI
from typing import Optional, Dict, Callable, List, Tuple

# 获取项目根目录
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# 将项目根目录添加到sys.path
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from app.utils.prompt import SEARCH_PROMPT
from config import base_config as config
from config.logging_config import logger
from app.utils.tools import get_time, response2json
from app.chat.chat_summary import summary
from app.search.search_searxng_api import search_api_worker
from app.utils.url2txt import url_to_markdown
from app.utils.compress_content import compress_url_content
from app.search.search_after_ai import evaluate_single_batch

class Style:
    PASS = "✅"
    FAIL = "❌"
    RUNNING = "🚀"
    SUMMARY = "📊"
    TIME = "⏱️"
    SUCCESS = "🎉"
    FAILURE = "💔"
    WARN = "⚠️"
    INFO = "ℹ️"
    RED = '\033[91m'
    GREEN = '\033[92m'
    ENDC = '\033[0m'
# --- 测试用例函数 (与之前相同) ---
# 每个测试函数在成功时应返回 True，失败时返回 False 或抛出异常
def search_api_worker_test():
    """测试 SearXNG API 搜索功能"""
    rsp = search_api_worker("linux do")
    if rsp:
        return True
def url_to_markdown_test():
    """测试 URL 内容抓取和转换为 Markdown 的功能"""
    rsp = url_to_markdown('https://www.aliyun.com/')
    if rsp:
        return True
def compress_url_content_test():
    """测试 URL 内容压缩总结功能"""
    rsp = compress_url_content('https://api-docs.deepseek.com/zh-cn/index.html', user_input="获取deepseek的联系方式")
    if rsp:
        return True
    
def search_plan_test():
    """测试 AI 生成搜索计划的功能"""
    messages = [{'role': 'user', 'content': SEARCH_PROMPT.substitute(messages="[{'role': 'user', 'content': '帮我搜一下最近openai新发布的那个模型的信息'}]", current_time=get_time())}] 
    client = OpenAI(api_key=config.SEARCH_KEYWORD_API_KEY, base_url=config.SEARCH_KEYWORD_API_URL)
    llm_rsp = client.chat.completions.create(model=config.SEARCH_KEYWORD_MODEL, messages=messages, temperature=0.1)
    results = response2json(llm_rsp.choices[0].message.content)
    if results:
        return True
    
def evaluate_single_batch_test():
    """测试 AI 评估搜索结果相关性的功能"""
    batch = [{"url": "https://aliyun-china.com", "title": "...", "content": "..."}, {"url": "https://aliyunping.com", "title": "...", "content": "..."}]
    rsp = evaluate_single_batch(batch_idx=1, batch=batch, search_purpose="获取阿里云测试官网")
    if rsp:
        return True

def summary_test():
    """测试对话总结功能"""
    user_messages = [{"role": "user", "content": "你好,简短的介绍一下你自己吧"}]
    rsp = summary(user_messages)
    if rsp:
        return True

# --- 供 WebUI 调用的辅助函数 ---
def get_available_tests() -> List[str]:
    """返回当前可用的测试函数名称列表"""
    get_available_tests_list = ["search_api_worker_test", "url_to_markdown_test",
                                "compress_url_content_test", "search_plan_test",
                                "evaluate_single_batch_test", "summary_test"]
    return get_available_tests_list


def run_single_test(test_name: str) -> Tuple[bool, str]:
    """运行指定的测试函数并返回 (是否成功, 信息)"""
    test_functions: Dict[str, Callable] = {
        name: obj for name, obj in globals().items() if callable(obj) and name.endswith('_test')
    }
    if test_name not in test_functions:
        return False, f"Test '{test_name}' not found"

    try:
        result = test_functions[test_name]()
        if result:
            return True, "PASS"
        else:
            return False, "Test returned a falsy value"
    except Exception as e:
        logger.exception("Error running test %s", test_name)
        return False, str(e)
    
# --- 测试运行器 (核心修改部分) ---
def run_tests(specific_test_name: Optional[str] = None):
    """
    自动发现并运行测试。
    :param specific_test_name: 如果提供，则只运行具有该名称的测试。否则，运行所有测试。
    """
    # 动态发现所有以 _test 结尾的函数
    test_functions: Dict[str, Callable] = {
        name: obj for name, obj in globals().items() if callable(obj) and name.endswith('_test')
    }
    tests_to_run: Dict[str, Callable] = {}
    if specific_test_name:
        if specific_test_name in test_functions:
            tests_to_run = {specific_test_name: test_functions[specific_test_name]}
        else:
            print(f"\n{Style.FAIL} Error: Test '{specific_test_name}' not found.")
            print(f"{Style.INFO} Available tests are:")
            for name in test_functions:
                print(f"  - {name}")
            print("")
            return 1 # 返回失败退出码
    else:
        tests_to_run = test_functions
    passed_count = 0
    failed_count = 0
    
    print("\n" + "="*50)
    print("           STARTING INTEGRATION TESTS")
    print("="*50 + "\n")
    start_time = time.time()
    for test_name, test_func in tests_to_run.items():
        print(f"{Style.RUNNING} Running: {test_name}")
        docstring = test_func.__doc__ or "No description."
        print(f"   {Style.INFO} {docstring.strip()}")
        
        try:
            result = test_func()
            if result:
                print(f"   {Style.PASS} {Style.GREEN}PASS{Style.ENDC}\n")
                passed_count += 1
            else:
                print(f"   {Style.FAIL} {Style.RED}FAIL{Style.ENDC} - Test returned a falsy value.\n")
                failed_count += 1
        except Exception as e:
            print(f"   {Style.FAIL} {Style.RED}ERROR{Style.ENDC} - An exception occurred:")
            traceback.print_exc()
            print("") # 换行
            failed_count += 1
            
    end_time = time.time()
    total_time = end_time - start_time
    total_tests = len(tests_to_run)
    print("-" * 50)
    print(f"             {Style.SUMMARY} TEST SUMMARY")
    print("-" * 50)
    print(f"Total Tests: {total_tests}")
    print(f"{Style.PASS} Passed: {passed_count}")
    print(f"{Style.FAIL} Failed: {failed_count}")
    print(f"{Style.TIME} Duration: {total_time:.2f} seconds")
    
    if failed_count > 0:
        print(f"\n{Style.FAILURE} 出现一些错误,请查看日志尝试修复\n")
        return 1
    else:
        print(f"\n{Style.SUCCESS} 所有测试均通过!\n")
        return 0
# 如果直接运行此文件，也执行测试
if __name__ == '__main__':
    # 允许从命令行传递一个测试名称
    test_to_run = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(run_tests(specific_test_name=test_to_run))