from pathlib import Path
import sys
from typing import Generator
from threading import Thread
from queue import Empty, Queue

# 将项目根目录添加到sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from app.chat.functions import process_messages_stream
from config.logging_config import logger
from config import base_config as config

def add_work(gen:Generator,q:Queue):
    try:
        for data in gen:
            logger.debug(data)
            q.put(data)
    except Exception as e:
        logger.error(f"出现问题{e}")
    finally:
        q.put("no data")

def process_messages_stream_heartbeat(messages,search_mode):
    data_queue = Queue()
    gen = process_messages_stream(messages,search_mode)
    t = Thread(target=add_work,args=(gen,data_queue))
    t.start()
    while True:
        try:
            data = data_queue.get(timeout=config.HEARTBEAT_TIMEOUT)
            if data == "no data":
                break
            
            yield data
        except Empty:
            yield ":heartbeat\n\n"
    t.join()
