from flask import Flask
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入配置和路由
from app.utils.config import BASE_CHAT_MODEL
from app.api.routes import register_routes

# 创建 Flask 应用
app = Flask(__name__)

# 注册路由
register_routes(app)

# 打印初始信息
print(f"基础对话使用的模型: {BASE_CHAT_MODEL}")

if __name__ == "__main__":
    # 运行 Flask 服务
    app.run(host="0.0.0.0", port=5000)