
import json
import threading
from flask import current_app
from flask_apscheduler import APScheduler
from flask_socketio import SocketIO

from demo_text import create_app
from demo_text import redis_store
from settings import Config

app = create_app()

scheduler = APScheduler()
scheduler.init_app(app)

if scheduler.state == 0:
    scheduler.start()

thread1 = None
thread2 = None
thread3 = None
thread_lock = threading.Lock()


def conn_info(socketio):
    while True:
        socketio.sleep(0.01)
        try:
            conn_change = redis_store.rpop('conn_change')
            if conn_change:
                socketio.emit('server_response', {'type': 3}, namespace='/info')
        except Exception as e:
            current_app.logger.error(e)

def get_data_list(socketio):
    global thread1, thread2
    with thread_lock:
        if thread2 is None:
            thread2 = socketio.start_background_task(conn_info, socketio)


if __name__ == '__main__':
    from demo_text.utils.utils import loop_task

    scheduler.add_job(func=loop_task, id='loop_task', jobstore='redis', replace_existing=True,
                      trigger='cron', day_of_week='0-6', hour=0, minute=0, second=0)

    # 配置socket服务
    socketio = SocketIO(app, cors_allowed_origins="*")
    async_mode = 'eventlet'
    socketio.init_app(app, async_mode=async_mode)

    socketio.start_background_task(get_data_list, socketio)

    # 启动api server
    socketio.run(app, host=Config.HTTP_HOST, port=Config.HTTP_PORT, log_output=True)