import sys
from flask import Flask
from waitress import serve

from app.utils.test_api import run_tests
from config.logging_config import logger
from config.base_config import BASE_CHAT_MODEL
from app.api.routes import register_routes

# 创建 Flask 应用
app = Flask(__name__)

# 注册路由
register_routes(app)

# 打印初始信息
logger.info(f"基础对话使用的模型: {BASE_CHAT_MODEL}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() == '--test':
        logger.info("开始执行测试...")
        
        test_to_run = sys.argv[2] if len(sys.argv) > 2 else None
        
        # 执行测试并获取退出码
        exit_code = run_tests(specific_test_name=test_to_run)
        
        # 使用 sys.exit 将测试结果（成功0/失败1）作为程序的退出码
        sys.exit(exit_code)
    else:
        # 如果没有 'test' 参数，正常启动服务
        logger.info("如果你不知道API是否填写正确,可执行 python main.py --test进行测试")
        logger.info("启动服务中.....")
        serve(app, host="0.0.0.0", port=5000, threads=8)