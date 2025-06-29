from pathlib import Path
import sys
import time
from flask import redirect, request, jsonify, make_response, Response, stream_with_context

# 将项目根目录添加到sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from app.api.sse_add_heartbeat import process_messages_stream_heartbeat
from app.utils.prompt import SYS_PROMPT
from app.utils.tools import get_time
from app.chat.functions import process_messages,process_messages_stream
from config.base_config import SUMMARY_MODEL,API_KEY

SHOW_MODEL = "search-llm"

def register_routes(app):
    @app.route("/", methods=["GET"])
    def index():
        return redirect("/setting")
    @app.route("/v1/chat/completions", methods=["POST"])
    def chat_completions_api():
        search_mode = 1
        # 校验 API key
        auth = request.headers.get("Authorization", "")
        if auth != f"Bearer {API_KEY}":
            return make_response(jsonify({"error": f"Invalid API Key {auth}"}), 401)
        
        data = request.get_json()
        if "deep-research" in data.get("model"):
            search_mode = 2
        if not data or "messages" not in data:
            return make_response(jsonify({"error": "传入数据有问题!"}), 400)
        
        messages = [msg for msg in data["messages"] if msg.get('role') != 'system']
        messages = [{'role': 'system', 'content': SYS_PROMPT.substitute(current_time=get_time())}] + messages
        # 检查 stream 参数
        STREAM_MODE = data.get("stream", False)
        if STREAM_MODE:
            rsp_stream = process_messages_stream_heartbeat(messages,search_mode=search_mode)
            return Response(stream_with_context(rsp_stream), mimetype='text/event-stream', headers={
                'Cache-Control': 'no-cache'
            })
        else:
            # 以第一个role为用户角色的消息为用户输入
            # print(messages)
            assistant_message = process_messages(messages)
            # print("--------------------------------")
            # print(assistant_message)
            # 构造 OpenAI 格式返回内容
            response_payload = {
                "id": "chatcmpl-123",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": SHOW_MODEL,
                "choices": [
                    {
                        "index": 0,
                        "message": assistant_message,
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }
            return jsonify(response_payload)

    @app.route("/v1/models", methods=["GET"])
    def models_api():
        # 校验 API key
        auth = request.headers.get("Authorization", "")
        if auth != f"Bearer {API_KEY}":
            return make_response(jsonify({"error": f"Invalid API Key {auth}"}), 401)
        
        models = {
            "data": [
                {"id": f"{SUMMARY_MODEL}-search", "object": "model", "owned_by": "cat3399"},
                {"id": f"{SUMMARY_MODEL}-deep-research", "object": "model", "owned_by": "cat3399"},
            ]
        }
        return jsonify(models)