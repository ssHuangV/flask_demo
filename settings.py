import logging
import os

import pymysql
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from yaml import load

try:
    from yaml import Cloader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

pymysql.install_as_MySQLdb()


class YAMLConfig(object):
    """
    解析系统配置文件
    """

    @staticmethod
    def parse_app_config(path, filename):
        file_path = "{}/{}".format(path, filename)
        if not os.path.exists(file_path):
            YAMLConfig.write(
                DefaultConfig.get_app_default_config(), path, filename)
        with open(file_path, 'r') as fh:
            return load(fh, Loader=Loader)

    """
    写入默认数据
    """

    @staticmethod
    def write(data, path, filename):
        if not os.path.exists(path):
            os.makedirs(path)

        with open("{}/{}".format(path, filename), 'w') as fh:
            return fh.write(data)


class DefaultConfig(object):
    @staticmethod
    def get_app_default_config():
        return """# the default config of demo_text system
# app config
APP_ENV: dev
APP_NAME: demo_text
DEBUG: False
# log setting config
LOG_BASE_PATH: /tmp/demo_text
LOG_LEVEL: error
LOG_SIZE: 50
LOG_COUNT: 2
LOG_MANAGER_CONFIG:
    LOG_HANDLERS:
        - name: system_log
          file: 'demo_text/autopilot_{time:YYYY-MM-DD}.log'
          filter: system
          options:
            retention: '30 days'
            format: '{time:X}|{message}'
# database config
DATABASE:
    DEFAULT:
        USER: root
        PASSWORD: 123456
        HOST: 127.0.0.1
        PORT: 3306
        DATABASE: demo_text
    MASTER:
        USER: root
        PASSWORD: 123456
        HOST: 127.0.0.1
        PORT: 3306
        DATABASE: demo_text
# redis config
REDIS_HOST: 127.0.0.1
REDIS_PORT: 6379
REDIS_DB: 6
REDIS_CLUSTER_FLAG: False
EXPIRATION: 86400
APP_EXPIRATION: 604800
PERMANENT_SESSION_LIFETIME: 86400
# SESSION_TYPE: redis
### http server config
HTTP_PORT: 9090
HTTP_HOST: 127.0.0.1

"""


class ConfigManager(object):
    def __new__(cls):
        if not hasattr(cls, '_instance'):
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self):
        # conf = YAMLConfig.parse_app_config(
        #     "{}/{}".format(os.path.expanduser('~'), ".demo_text"), 'demo_text.yaml')
        conf = YAMLConfig.parse_app_config(os.getcwd(), 'demo_text.yaml')
        conf['LOG_LEVEL'] = getattr(logging, conf['LOG_LEVEL'].upper())

        # 数据库配置
        if 'SQLALCHEMY_DATABASE_URI' not in conf:
            conf[
                'SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}?charset=utf8mb4'.format(
                **conf['DATABASE']['DEFAULT'])
        if 'MASTER' in conf['DATABASE'] and 'MASTER_DATABASE_URI' not in conf:
            conf[
                'MASTER_DATABASE_URI'] = 'mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}?charset=utf8mb4'.format(
                **conf['DATABASE']['MASTER'])

        conf['SQLALCHEMY_POOL_SIZE'] = 40
        conf['SQLALCHEMY_POOL_TIMEOUT'] = 30
        conf['SQLALCHEMY_POOL_RECYCLE'] = 3600
        conf['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        conf['REDIS_KEY_ACTUAL_DELAY'] = "actual_delay"
        conf['REDIS_KEY_PROPERTY'] = "property"
        conf['REDIS_KEY_EVENT_SERVICE'] = "event_service"

        conf['SCHEDULER_JOBSTORES'] = {
            'redis': RedisJobStore(db=conf['REDIS_DB'], host=conf['REDIS_HOST'], port=conf['REDIS_PORT']),
            'mysql': SQLAlchemyJobStore(url="mysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}?charset=utf8".format(
                **conf['DATABASE']['DEFAULT']))
        }

        self.__dict__ = conf


Config = ConfigManager()
