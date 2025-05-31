from pathlib import Path
import sys
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import uvicorn

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))


from app.utils.config import SUMMARY_API_KEY, SUMMARY_API_URL, SUMMARY_MODEL
from app.utils.tools import sse_create_openai_usage_data, sse_create_openai_data

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    # 获取请求数据
    data = await request.json()
    
    # 创建OpenAI客户端
    client = OpenAI(
        api_key=SUMMARY_API_KEY,
        base_url=SUMMARY_API_URL,
    )
    
    # 从请求中获取参数
    messages = data.get("messages", [])
    temperature = data.get("temperature", 1.0)
    stream = data.get("stream", True)
    print(messages)
    # 创建完成请求
    completion = client.chat.completions.create(
        model=SUMMARY_MODEL,
        messages=messages,
        stream=stream,
        temperature=temperature,
        stream_options={"include_usage": True}
    )
    
    # 生成流式响应
    def generate():
        for chunk in completion:
            try:
                if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content:
                    yield sse_create_openai_data(reasoning_content=chunk.choices[0].delta.reasoning_content)
                
                if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                    yield sse_create_openai_data(content=chunk.choices[0].delta.content)
            except:
                pass
        # 在结束时添加使用情况
        try:
            usage = {
                "completion_tokens": chunk.usage.completion_tokens,
                "prompt_tokens": chunk.usage.prompt_tokens,
                "total_tokens": chunk.usage.total_tokens
            }
            print(usage)
            yield sse_create_openai_usage_data(usage)
            yield "data: [DONE]\n\n"
        except:
            pass
    
    return StreamingResponse(generate(), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)