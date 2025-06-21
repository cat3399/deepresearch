import sys
from pathlib import Path

# --- 配置和路径设置 ---
# 将项目根目录添加到sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from config.logging_config import logger
# 黑名单文件路径 (假设在项目根目录)
BLACKLIST_FILE = ROOT_DIR / 'blacklist.txt'

def load_blacklist(filepath):
    """从文件加载 URL 黑名单到集合中以提高效率"""
    blacklist = set()
    if not filepath.exists():
        logger.warning(f"黑名单文件 '{filepath}' 不存在。将不进行 URL 黑名单过滤。")
        return blacklist
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                url = line.strip()
                if url: # 忽略空行
                    blacklist.add(url)
        logger.info(f"成功从 '{filepath}' 加载 {len(blacklist)} 个 URL 到黑名单。")
    except IOError as e:
        logger.error(f"读取黑名单文件 '{filepath}' 时出错: {e}")
        # 出错时返回空集合，避免影响正常流程，但会记录错误
    return list(blacklist)

URL_BLACKLIST = load_blacklist(BLACKLIST_FILE)
logger.debug(URL_BLACKLIST)
