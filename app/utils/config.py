import os
from string import Template
from dotenv import load_dotenv
from pathlib import Path

# 将项目根目录添加到sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
env_path = ROOT_DIR.joinpath(".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
    print("环境变量文件已加载")

# class ModelConfig

# SearXNG配置（需要支持JSON格式）
SEARXNG_URL = os.getenv("SEARXNG_URL")
SEARCH_API_LIMIT = int(os.getenv("SEARCH_API_LIMIT"))
#############################################
# 网页爬虫配置
#############################################
# 只填一个也行,两个都填会优先使用FireCrawl 在出错或者抓取内容过少时会换用Crawl4AI（感觉FireCrawl还是快些,虽然CRAWL4AI宣称更快）
# FireCrawl配置
 #使用官方API留空
FIRECRAWL_API_URL = os.getenv("FIRECRAWL_API_URL", "https://api.firecrawl.dev")
 # 本地使用可以不填 调用官方API需要填
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
# Crawl4AI配置
CRAWL4AI_API_URL = os.getenv("CRAWL4AI_API_URL")
FIRECRAWL_API_URL = FIRECRAWL_API_URL.rstrip('/')
if FIRECRAWL_API_URL == "https://api.firecrawl.dev" and not FIRECRAWL_API_KEY:
    print("使用Firecrawl需要填写key 从https://www.firecrawl.dev/获取")
    FIRECRAWL_API_URL = ''

if not FIRECRAWL_API_URL and not CRAWL4AI_API_URL:
    print("至少需要填写一种获取网页内容的方式")
    raise ValueError("至少需要填写一种获取网页内容的方式")
CRAWL_THREAD_NUM = int(os.getenv("CRAWL_THREAD_NUM"))
MAX_SEARCH_RESULTS = int(os.getenv("MAX_SEARCH_RESULTS"))
#############################################
# 模型配置
#############################################
# 基础对话模型配置（需要支持function calling,模型性能差一些也无所谓,只是调用联网搜索的函数）
BASE_CHAT_API_KEY = os.getenv("BASE_CHAT_API_KEY")
BASE_CHAT_API_URL = os.getenv("BASE_CHAT_API_URL")
BASE_CHAT_MODEL = os.getenv("BASE_CHAT_MODEL")

# 生成联网搜索关键词的模型配置（留空表示和基础对话模型相同）
SEARCH_KEYWORD_API_KEY = os.getenv("SEARCH_KEYWORD_API_KEY", BASE_CHAT_API_KEY)
SEARCH_KEYWORD_API_URL = os.getenv("SEARCH_KEYWORD_API_URL", BASE_CHAT_API_URL)
SEARCH_KEYWORD_MODEL = os.getenv("SEARCH_KEYWORD_MODEL", BASE_CHAT_MODEL)

# 评估网页价值的模型配置
EVALUATE_THREAD_NUM = int(os.getenv("EVALUATE_THREAD_NUM", 5))
EVALUATE_API_KEY=os.getenv("EVALUATE_API_KEY", BASE_CHAT_API_KEY)
EVALUATE_API_URL=os.getenv("EVALUATE_API_URL", BASE_CHAT_API_URL)
EVALUATE_MODEL=os.getenv("EVALUATE_MODEL", BASE_CHAT_MODEL)

# 网页内容压缩提取模型配置（最好选择输出最快的服务商,并且允许长输入输出） 
 # 选择GEMINI或OPENAI格式的API URL,默认使用GEMINI模型 如果使用gemini只有一个api key的时候会报429错误 建议至少两个
COMPRESS_API_TYPE = os.getenv("COMPRESS_API_TYPE")
COMPRESS_API_KEY = os.getenv("COMPRESS_API_KEY")
COMPRESS_API_URL = os.getenv("COMPRESS_API_URL")
COMPRESS_MODEL = os.getenv("COMPRESS_MODEL")

# 最后总结搜索结果的模型配置（留空表示和基础对话模型相同）
SUMMARY_API_TYPE = os.getenv("SUMMARY_API_TYPE")
SUMMARY_API_KEY = os.getenv("SUMMARY_API_KEY", BASE_CHAT_API_KEY)
SUMMARY_API_URL = os.getenv("SUMMARY_API_URL", BASE_CHAT_API_URL)
SUMMARY_MODEL = os.getenv("SUMMARY_MODEL", BASE_CHAT_MODEL)

MAX_RESEARCH_NUM = 3

#############################################
# 配置校验
#############################################

def validate_config():
    """验证配置项是否有效"""
    errors = []
    warnings = []
    
    # 检查基础搜索引擎
    if not SEARXNG_URL:
        errors.append("缺少SearXNG URL配置")
    
    # 检查基础对话模型配置
    if not BASE_CHAT_API_KEY:
        errors.append("缺少基础对话模型API密钥")
    if not BASE_CHAT_API_URL:
        errors.append("缺少基础对话模型API地址")
    if not BASE_CHAT_MODEL:
        errors.append("缺少基础对话模型名称")
    
    # 检查关键词模型配置
    if not SEARCH_KEYWORD_API_KEY or not SEARCH_KEYWORD_API_URL or not SEARCH_KEYWORD_MODEL:
        warnings.append("使用基础对话模型作为搜索关键词生成模型")
    
    # 检查压缩模型配置
    if not COMPRESS_API_KEY:
        errors.append("缺少网页内容压缩提取模型API密钥")
    if not COMPRESS_API_URL:
        errors.append("缺少网页内容压缩提取模型API地址")
    if not COMPRESS_MODEL:
        errors.append("缺少网页内容压缩提取模型名称")
    
    # 检查总结模型配置
    if not SUMMARY_API_KEY or not SUMMARY_API_URL or not SUMMARY_MODEL:
        warnings.append("使用基础对话模型作为总结模型")
    
    # 输出校验结果
    if errors:
        print("\n====== 配置错误 ======")
        for error in errors:
            print(f"❌ {error}")
        print("\n程序将无法正常运行,请修复上述错误。")
        return False
    
    if warnings:
        print("\n====== 配置警告 ======")
        for warning in warnings:
            print(f"⚠️ {warning}")
    
    print("\n✅ 配置校验通过")
    
    return True

# 检查配置项完整性
CONFIG_VALID = validate_config()
