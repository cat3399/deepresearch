from flask import Flask
from waitress import serve
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
    # 运行 Flask 服务
    # app.run(host="0.0.0.0", port=5000)
    logger.info("启动服务中.....")
    serve(app, host="0.0.0.0", port=5000, threads=8)
