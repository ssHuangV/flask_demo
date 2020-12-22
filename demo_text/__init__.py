
import os
import sys

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis

from log import LoggerManager, setup_log
from settings import Config
from .exceptions import handle_exception
from .middlewares import MiddlewareManger
from .utils.db import DBManager
from .utils.response import Response

db = SQLAlchemy()
middle_manger = MiddlewareManger()
log_manager = LoggerManager()
setup_log()

redis_store = StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, db=Config.REDIS_DB, decode_responses=True)

def create_app():
    if getattr(sys, 'frozen', False):
        template_folder = os.path.join(sys._MEIPASS, 'templates')
        static_folder = os.path.join(sys._MEIPASS, 'static')
        app = Flask(__name__, template_folder=template_folder,
                    static_folder=static_folder, static_url_path='')
    else:
        app = Flask(__name__, static_url_path='')

    app.config.from_object(Config)
    # Session(app)
    # 跨域
    CORS(app, supports_credentials=True)
    # CORS(app)

    db.init_app(app)

    middle_manger.init_app(app)

    @app.errorhandler(Exception)
    def handle_exceptions(error):
        return handle_exception(error)

    @app.route('/')
    def index():
        return Response.success(Config.APP_NAME)

    from demo_text.controllers import (
        taskmode_blue
    )
    API_PREFIX = '/api'
    app.register_blueprint(taskmode_blue, url_prefix=API_PREFIX)

    return app


__all__ = ['db', 'redis_store', 'create_app']