from pathlib import Path
import sys
from typing import Generator
from threading import Event, Thread
from queue import Empty, Queue

# 将项目根目录添加到sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from app.chat.functions import process_messages_stream
from config.logging_config import logger
from config import base_config as config

def add_work(gen: Generator, q: Queue, stop_event: Event):
    """
    一个可以被外部事件停止的工作函数。
    """
    try:
        for data in gen:
            # 在每次循环前检查是否需要停止
            if stop_event.is_set():
                logger.info("检测到停止信号，后台工作线程退出。")
                break
            logger.debug(data)
            q.put(data)
    except Exception as e:
        logger.error(f"后台工作线程出现问题: {e}")
    finally:
        # 确保队列的消费者（主线程）知道数据已结束
        q.put("no data")

def process_messages_stream_heartbeat(messages, search_mode):
    data_queue = Queue()
    stop_event = Event()  # <-- 1. 创建事件对象，作为线程间的通信信号
    gen = process_messages_stream(messages, search_mode)
    
    # <-- 2. 将事件对象传递给后台线程
    t = Thread(target=add_work, args=(gen, data_queue, stop_event))
    t.start()
    
    try:
        while True:
            try:
                data = data_queue.get(timeout=config.HEARTBEAT_TIMEOUT)
                if data == "no data":
                    break  # 正常结束
                
                yield data
            except Empty:
                # 超时，发送心跳以保持连接
                yield ":heartbeat\n\n"
    finally:
        # 无论是因为正常结束、出错还是客户端断开连接，finally 块都会被执行
        logger.info("主生成器即将退出，正在通知后台线程停止...")
        stop_event.set()  # 设置停止信号
        
        # 等待后台线程执行完毕，可以设置一个超时以防万一
        t.join(timeout=5) 
        if t.is_alive():
            logger.warning("后台线程在5秒内未能正常停止。")
