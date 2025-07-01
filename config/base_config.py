import os
import shutil
import sys
import random
from dotenv import load_dotenv
from pathlib import Path

# 将项目根目录添加到sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))
from config.logging_config import logger

env_path = ROOT_DIR.joinpath(".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
    logger.info("环境变量文件已加载")
else:
    template_path = ROOT_DIR.joinpath(".env.template")
    if os.path.exists(template_path):
        shutil.copy(template_path, env_path)
        load_dotenv(env_path)
        logger.info("未找到.env文件，已从模板复制一份")
    else:
        logger.error("未找到.env文件，也没有找到模板文件")


def get_random_api_key(api_key_str):
    """从逗号分隔的API密钥字符串中随机选择一个
    
    Args:
        api_key_str: 逗号分隔的API密钥字符串，如 "key1,key2,key3"
        
    Returns:
        随机选择的API密钥，如果输入为空则返回空字符串
    """
    if not api_key_str:
        return ""
    
    keys = [key.strip() for key in api_key_str.split(',') if key.strip()]
    if not keys:
        return ""
    
    selected_key = random.choice(keys)
    if len(keys) > 1:
        logger.info(f"从 {len(keys)} 个API密钥中随机选择了一个")
    
    return selected_key

# 首先加载所有环境变量
# ... (此处省略了其他非模型变量的加载，它们保持不变) ...

API_KEY = os.getenv("API_KEY", "sk-1")

#############################################
# 搜索引擎配置
#############################################
# SearXNG配置（需要支持JSON格式）
SEARXNG_URL = os.getenv("SEARXNG_URL")
SEARCH_API_LIMIT = os.getenv("SEARCH_API_LIMIT")
if SEARCH_API_LIMIT:
    SEARCH_API_LIMIT = int(SEARCH_API_LIMIT)

# tavily 配置
TAVILY_KEY = get_random_api_key(os.getenv("TAVILY_KEY", ""))
TAVILY_MAX_NUM = os.getenv("TAVILY_MAX_NUM","20")
#############################################
# 网页爬虫配置
#############################################
# 只填一个也行,两个都填会优先使用FireCrawl 在出错或者抓取内容过少时会换用Crawl4AI

# FireCrawl配置
FIRECRAWL_API_URL = os.getenv("FIRECRAWL_API_URL")
FIRECRAWL_API_KEY = get_random_api_key(os.getenv("FIRECRAWL_API_KEY"))

# 如果用户提供了API Key但URL为空或未设置，则默认为官方URL
if FIRECRAWL_API_KEY and not FIRECRAWL_API_URL:
    FIRECRAWL_API_URL = "https://api.firecrawl.dev"
    logger.info("检测到FireCrawl API Key但未配置URL，已自动设置为官方API URL: https://api.firecrawl.dev")

# 如果URL是官方URL但没有Key，则警告并视作无效配置，Crawl4AI将作为备选或唯一选项
if FIRECRAWL_API_URL and FIRECRAWL_API_URL.rstrip('/') == "https://api.firecrawl.dev" and not FIRECRAWL_API_KEY:
    logger.warning("使用Firecrawl官方API (https://api.firecrawl.dev) 需要填写 FIRECRAWL_API_KEY。此FireCrawl配置将视为无效。")
    FIRECRAWL_API_URL = '' # 清空，使其在后续检查中被视为未配置

# Crawl4AI配置
CRAWL4AI_API_URL = os.getenv("CRAWL4AI_API_URL")

# Jina配置
JINA_API_URL = os.getenv("JINA_API_URL")
JINA_API_KEY = os.getenv("JINA_API_KEY")

# 统一处理URL末尾的斜杠
if FIRECRAWL_API_URL:
    FIRECRAWL_API_URL = FIRECRAWL_API_URL.rstrip('/')
if CRAWL4AI_API_URL:
    CRAWL4AI_API_URL = CRAWL4AI_API_URL.rstrip('/')
if JINA_API_URL:
    JINA_API_URL = JINA_API_URL.rstrip('/')

CRAWL_THREAD_NUM = int(os.getenv("CRAWL_THREAD_NUM", "5"))
MAX_SEARCH_RESULTS = int(os.getenv("MAX_SEARCH_RESULTS", "6"))
MAX_DEEPRESEARCH_RESULTS = int(os.getenv("MAX_DEEPRESEARCH_RESULTS","3"))
MAX_STEPS_NUM = int(os.getenv("MAX_STEPS_NUM", "12"))

#############################################
# 模型配置
#############################################

# 基础对话模型配置（需要支持function calling）
BASE_CHAT_API_KEY = get_random_api_key(os.getenv("BASE_CHAT_API_KEY"))
BASE_CHAT_API_URL = os.getenv("BASE_CHAT_API_URL")
BASE_CHAT_MODEL = os.getenv("BASE_CHAT_MODEL")

# 生成联网搜索关键词的模型配置（留空表示和基础对话模型相同）
SEARCH_KEYWORD_API_KEY = get_random_api_key(os.getenv("SEARCH_KEYWORD_API_KEY", os.getenv("BASE_CHAT_API_KEY", "")))
SEARCH_KEYWORD_API_URL = os.getenv("SEARCH_KEYWORD_API_URL", BASE_CHAT_API_URL)
SEARCH_KEYWORD_MODEL = os.getenv("SEARCH_KEYWORD_MODEL", BASE_CHAT_MODEL)

# 评估网页价值的模型配置
EVALUATE_THREAD_NUM = int(os.getenv("EVALUATE_THREAD_NUM", 5))
EVALUATE_API_KEY = get_random_api_key(os.getenv("EVALUATE_API_KEY", os.getenv("BASE_CHAT_API_KEY", "")))
EVALUATE_API_URL = os.getenv("EVALUATE_API_URL", BASE_CHAT_API_URL)
EVALUATE_MODEL = os.getenv("EVALUATE_MODEL", BASE_CHAT_MODEL)

# 网页内容压缩提取模型配置（最好选择输出最快的服务商,并且允许长输入输出） 
 # 选择GEMINI或OPENAI格式的API URL,默认使用GEMINI模型 如果使用gemini只有一个api key的时候会报429错误 建议至少两个
COMPRESS_API_TYPE = os.getenv("COMPRESS_API_TYPE")
if COMPRESS_API_TYPE:
    COMPRESS_API_TYPE = COMPRESS_API_TYPE.upper()
COMPRESS_API_KEY = get_random_api_key(os.getenv("COMPRESS_API_KEY"))
COMPRESS_API_URL = os.getenv("COMPRESS_API_URL","https://generativelanguage.googleapis.com")
COMPRESS_MODEL = os.getenv("COMPRESS_MODEL")

# 最后总结搜索结果的模型配置（留空表示和基础对话模型相同）
SUMMARY_API_TYPE = os.getenv("SUMMARY_API_TYPE")
if SUMMARY_API_TYPE:
    SUMMARY_API_TYPE = SUMMARY_API_TYPE.upper()
SUMMARY_API_KEY = get_random_api_key(os.getenv("SUMMARY_API_KEY", os.getenv("BASE_CHAT_API_KEY", "")))
SUMMARY_API_URL = os.getenv("SUMMARY_API_URL", BASE_CHAT_API_URL)
SUMMARY_MODEL = os.getenv("SUMMARY_MODEL", BASE_CHAT_MODEL)

# --- 智能默认值逻辑开始 ---
# 2. 如果设置了 ALL_IN_GEMINI_KEY，则为未设置的选项提供默认值
ALL_IN_GEMINI_KEY = os.getenv("ALL_IN_GEMINI_KEY")
if ALL_IN_GEMINI_KEY:
    logger.info("检测到 ALL_IN_GEMINI_KEY，将为未配置的模型选项提供Gemini默认值。")
    gemini_key_str = os.getenv("ALL_IN_GEMINI_KEY")

    # 定义Gemini默认值
    # OpenAI兼容格式
    openai_compatible_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
    model_pro_openai = "models/gemini-2.5-pro"
    model_flash_openai = "models/gemini-2.5-flash"
    
    # 原生Gemini格式
    native_gemini_url = "https://generativelanguage.googleapis.com"
    model_flash_native = "gemini-2.5-flash-lite-preview-06-17"
    native_gemini_type = "GEMINI"

    # --- 为每个模型组按需应用默认值 ---
    
    # 基础与关键词模型 (Pro)
    if not BASE_CHAT_API_KEY: BASE_CHAT_API_KEY = get_random_api_key(gemini_key_str)
    if not BASE_CHAT_API_URL: BASE_CHAT_API_URL = openai_compatible_url
    if not BASE_CHAT_MODEL: BASE_CHAT_MODEL = model_pro_openai
    # 由于关键词模型默认跟随基础模型，只需确保基础模型有值即可
    if not SEARCH_KEYWORD_API_KEY: SEARCH_KEYWORD_API_KEY = BASE_CHAT_API_KEY
    if not SEARCH_KEYWORD_API_URL: SEARCH_KEYWORD_API_URL = BASE_CHAT_API_URL
    if not SEARCH_KEYWORD_MODEL: SEARCH_KEYWORD_MODEL = BASE_CHAT_MODEL

    # 评估模型 (Flash, OpenAI兼容接口)
    if not EVALUATE_API_KEY: EVALUATE_API_KEY = get_random_api_key(gemini_key_str)
    if not EVALUATE_API_URL: EVALUATE_API_URL = openai_compatible_url
    if not EVALUATE_MODEL: EVALUATE_MODEL = model_flash_openai

    # 压缩模型 (Flash, 原生接口)
    if not COMPRESS_API_KEY: COMPRESS_API_KEY = get_random_api_key(gemini_key_str)
    if not COMPRESS_API_URL: COMPRESS_API_URL = native_gemini_url
    if not COMPRESS_MODEL: COMPRESS_MODEL = model_flash_native
    if not COMPRESS_API_TYPE: COMPRESS_API_TYPE = native_gemini_type

    # 总结模型 (Pro)
    if not SUMMARY_API_KEY: SUMMARY_API_KEY = get_random_api_key(gemini_key_str)
    if not SUMMARY_API_URL: SUMMARY_API_URL = openai_compatible_url
    if not SUMMARY_MODEL: SUMMARY_MODEL = model_pro_openai
    if not SUMMARY_API_TYPE: SUMMARY_API_TYPE = "OPENAI" # OpenAI兼容接口的类型

    logger.info("All-in-Gemini 默认值已应用。在 .env 中明确设置的选项已被保留。")
# --- 智能默认值逻辑结束 ---


AVAILABLE_EXTENSIONS = ['.pdf', '.docx', '.doc', '.xlsx', '.xls']
HEARTBEAT_TIMEOUT = int(os.getenv("HEARTBEAT_TIMEOUT",25))

#############################################
# 配置校验
#############################################

def validate_config():
    """验证配置项是否有效"""
    errors = []
    warnings = []
    
    # 1. 搜索引擎配置校验
    if not SEARXNG_URL and not TAVILY_KEY:
        errors.append("至少需要配置一种搜索引擎: SearXNG URL 或 Tavily KEY。")
    elif not SEARXNG_URL:
        warnings.append("缺少 SearXNG URL 配置，将仅使用 Tavily (如果已配置)。")
    elif not TAVILY_KEY:
        warnings.append("缺少 Tavily KEY 配置，将仅使用 SearXNG (如果已配置)。")
    
    # 2. 网页爬虫配置校验
    if not FIRECRAWL_API_URL and not CRAWL4AI_API_URL and not JINA_API_URL:
        errors.append("至少需要配置一种有效的网页爬虫服务: FireCrawl 或 Crawl4AI 或 Jina")
    if not FIRECRAWL_API_URL:
        warnings.append("FireCrawl 配置无效或未提供")
    if not CRAWL4AI_API_URL:
        warnings.append("Crawl4AI 配置未提供")
    if not JINA_API_URL:
        warnings.append("Jina 配置未提供")

    # 3. 基础对话模型配置校验
    if not BASE_CHAT_API_KEY:
        errors.append("缺少基础对话模型API密钥 (BASE_CHAT_API_KEY)。")
    if not BASE_CHAT_API_URL:
        errors.append("缺少基础对话模型API地址 (BASE_CHAT_API_URL)。")
    if not BASE_CHAT_MODEL:
        errors.append("缺少基础对话模型名称 (BASE_CHAT_MODEL)。")
    
    # Helper to check if model configs fallback to BASE_CHAT
    def get_fallback_details(prefix, suffixes):
        details = []
        all_fallback_to_base = True
        # 如果ALL_IN_GEMINI_KEY存在，则不检查回退，因为默认值已经填充
        if ALL_IN_GEMINI_KEY:
            return [], False
        for suffix in suffixes:
            if os.getenv(f"{prefix}{suffix}") is None:
                details.append(suffix)
            else:
                all_fallback_to_base = False
        return details, all_fallback_to_base

    # 4. 搜索关键词模型配置校验
    search_fallback_details, search_all_fallback = get_fallback_details("SEARCH_KEYWORD_", ["API_KEY", "API_URL", "MODEL"])
    if search_all_fallback:
        warnings.append("搜索关键词生成模型配置未在.env中独立设置，将完全使用基础对话模型配置。")
    elif search_fallback_details:
        warnings.append(f"搜索关键词生成模型配置不完整，以下部分将使用基础对话模型配置: {', '.join(search_fallback_details)}。")

    # 5. 评估网页价值模型配置校验
    eval_fallback_details, eval_all_fallback = get_fallback_details("EVALUATE_", ["API_KEY", "API_URL", "MODEL"])
    if eval_all_fallback:
        warnings.append("评估网页价值模型配置未在.env中独立设置，将完全使用基础对话模型配置。")
    elif eval_fallback_details:
        warnings.append(f"评估网页价值模型配置不完整，以下部分将使用基础对话模型配置: {', '.join(eval_fallback_details)}。")

    # 6. 网页内容压缩提取模型配置校验 (这些不回退到BASE_CHAT)
    if not COMPRESS_API_KEY:
        errors.append("缺少网页内容压缩提取模型API密钥 (COMPRESS_API_KEY)。")
    if not COMPRESS_API_URL:
        errors.append("缺少网页内容压缩提取模型API地址 (COMPRESS_API_URL)。")
    if not COMPRESS_MODEL:
        errors.append("缺少网页内容压缩提取模型名称 (COMPRESS_MODEL)。")

    # 7. 总结搜索结果模型配置校验
    summary_fallback_details, summary_all_fallback = get_fallback_details("SUMMARY_", ["API_KEY", "API_URL", "MODEL"])
    summary_api_type_env = os.getenv("SUMMARY_API_TYPE")

    if summary_all_fallback and summary_api_type_env is None:
        warnings.append("总结搜索结果模型配置未在.env中独立设置，将完全使用基础对话模型配置 (且API类型未指定)。")
    elif summary_fallback_details:
        msg = f"总结搜索结果模型的核心配置不完整，以下部分将使用基础对话模型配置: {', '.join(summary_fallback_details)}。"
        if summary_api_type_env is None and not summary_all_fallback: 
            msg += " 此外，SUMMARY_API_TYPE 未设置。"
        warnings.append(msg)
    elif not summary_all_fallback and summary_api_type_env is None: 
        warnings.append("总结搜索结果模型已配置API_KEY/URL/MODEL，但 SUMMARY_API_TYPE 未设置。")
    
    if errors:
        logger.error("\n====== 配置错误 ======")
        for error in errors:
            logger.error(f"❌ {error}")
        logger.error("\n程序将无法正常运行,请修复上述错误。")
        return False
    
    if warnings:
        logger.warning("====== 配置警告 ======")
        for warning in warnings:
            logger.warning(f"⚠️ {warning}")
    
    logger.info("✅ 配置校验通过")
    
    return True

CONFIG_VALID = validate_config()
