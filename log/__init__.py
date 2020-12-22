import codecs
import datetime
import json
import logging
import os
import re
import time
from logging.handlers import BaseRotatingHandler

from flask import g
from loguru import logger

from demo_text.utils.getip import get_client_ip, ip2long, get_local_ip
from settings import Config


class LoggerManager():
    '''
    customer log manager class to deal all system logs
    '''

    def __init__(self):
        self.base_path = Config.LOG_BASE_PATH
        self.config = Config.LOG_MANAGER_CONFIG
        self.init()

    def init(self):
        '''initialize the logger information'''
        for handler in self.config['LOG_HANDLERS']:
            def filter_handler(record, filter_flag=handler['filter']):
                return filter_flag in record['extra']

            logger.add('{}/{}'.format(self.base_path, handler['file']), filter=filter_handler, **handler['options'])


class Log():
    @staticmethod
    def system(message):
        '''
        system log handler
        usage:
        Log.system([{level}, {content}, {params}, {ip}])
        :param level: 可选值 ERROR, INFO, WRAN, DEBUG
        :param content: 消息内容
        :param params: 参数值, 字典或json串
        :param ip: IP 本机ip
        '''
        if not isinstance(message, list) or len(message) != 3:
            raise Exception(
                'log format error, message should be list and not empty')

        if isinstance(message[2], dict) or isinstance(message[2], list):
            message[2] = json.dumps(message[2])
        message.append(str(ip2long(get_local_ip())))
        message.append(str(int(time.time() * 1000 * 1000)))
        logger.bind(system=True).info('|'.join(message))

    @staticmethod
    def operate(message):
        '''
        operate log handler
        usage:
        Log.operate([{user_id}, {username}, {bussiness}, {action}, {content}, {status}, {ip}])
        :param user_id: 操作者ID
        :param username: 操作者名称
        :param bussiness: 业务类型，可选值：应用管理（1）、产品管理（2）、设备管理（3）、在线调试（4）
        :param action: 动作，可选值：新增应用、编辑应用、删除应用、添加产品...
        :param content: 操作内容详情，json串
        :param status: 操作状态，1成功，2失败
        :param ip: IP 本机ip
        '''
        if not isinstance(message, list) or len(message) <= 0:
            raise Exception(
                'log format error, message should be list and not empty')

        if isinstance(message[4], dict) or isinstance(message[4], list):
            message[4] = json.dumps(message[4])
        message.append(str(ip2long(get_local_ip())))
        logger.bind(operate=True).info('|'.join(message))

    @staticmethod
    def device(message):
        '''
        device log handler
        usage:
        Log.device([{user_id}, {username}, {device_key}, {device_name}, {product_key}, {product_name}, {type}, {event},
         {content}, {status}, {ip}])
        :param user_id: 操作者ID
        :param username: 操作者名称
        :param device_key: 设备Key
        :param device_name: 设备名称
        :param product_key: 产品Key
        :param product_name: 产品名称
        :param type: 日志类型，可选值：1行为日志，2物模型日志
        :param event: 事件类型
        :param content: 日志内容
        :param status: 状态
        :param ip: IP 本机ip
        '''
        if not isinstance(message, list) or len(message) <= 0:
            raise Exception(
                'log format error, message should be list and not empty')

        if isinstance(message[8], dict) or isinstance(message[8], list):
            message[8] = json.dumps(message[8])
        message.append(str(ip2long(get_local_ip())))
        logger.bind(device=True).info('|'.join(message))


def record_operate_log(bussiness, action, content, status='成功'):
    try:
        user_id = str(g.user_id) if 'user_id' in g else '0'
        username = g.username if 'username' in g else 'None'
        content['client_ip'] = get_client_ip()
        Log.operate([user_id, username, bussiness, action, content, status])
    except Exception as e:
        params = {
            'type': '记录操作日志错误',
            'user_id': user_id if 'user_id' in dir() else '',
            'username': username if 'username' in dir() else '',
            'bussiness': bussiness,
            'action': action,
            'content': content,
            'status': status,
        }
        record_system_log(e, params, level='ERROR')


def record_system_log(content, params, level='ERROR', request=None):
    try:
        if not params.get('filename', None):
            params['filename'] = content.__traceback__.tb_frame.f_globals['__file__']
        if not params.get('lineno', None):
            params['lineno'] = content.__traceback__.tb_lineno
        if request:
            params['url'] = request.url
            params['args'] = request.args.to_dict()
            params['form'] = request.form.to_dict()
            params['headers'] = request.headers.to_wsgi_list()
            params['client_ip'] = get_client_ip()
        Log.system([level, str(content), params])
    except Exception as e:
        pass


class MQTTRecvLog(object):
    def __init__(self):
        self.recv_log_path_list = ['./logs/mqtt_recv.log', './logs/mqtt_recv1.log']
        self.recv_log_path = self.recv_log_path_list[0]

    def record_log(self, info_type, log_info):
        if os.path.exists(self.recv_log_path):
            size = os.path.getsize(self.recv_log_path)
            if size > 50 * 1024 * 1024:
                idx = self.recv_log_path_list.index(self.recv_log_path)
                if idx == 0:
                    self.recv_log_path = self.recv_log_path_list[1]
                else:
                    self.recv_log_path = self.recv_log_path_list[0]
                if os.path.exists(self.recv_log_path):
                    size = os.path.getsize(self.recv_log_path)
                    if size >= 50 * 1024 * 1024:
                        with open(self.recv_log_path, 'w') as f:
                            pass

        with open(self.recv_log_path, 'a') as f:
            now_time = datetime.datetime.now()
            f.write('time: {}, type:{}, info：{}\n'.format(now_time, info_type, log_info))
            f.write('=' * 40 + '\n')


class MidnightRotatingFileHandler(BaseRotatingHandler):
    def __init__(self, filename, backupCount=1, encoding=None):
        self.date = datetime.date.today()
        self.backupCount = backupCount
        self.suffix = '%Y-%m-%d'
        self.extMatch = r'^\d{4}-\d{2}-\d{2}(\.\w+)?$'
        self.extMatch = re.compile(self.extMatch, re.ASCII)
        self.dirName, self.baseName = os.path.split(os.path.abspath(filename))
        super(BaseRotatingHandler, self).__init__(filename, mode='a', encoding=encoding, delay=0)

    def shouldRollover(self, record):
        return self.date != datetime.date.today()

    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None
        self.date = datetime.date.today()
        if self.backupCount > 0:
            for s in self.getFilesToDelete():
                os.remove(s)

    def getFilesToDelete(self):
        fileNames = os.listdir(self.dirName)
        result = []
        prefix = '.' + self.baseName
        plen = len(prefix)
        for fileName in fileNames:
            if fileName[-plen:] == prefix:
                suffix = fileName[:-plen]
                if self.extMatch.match(suffix):
                    result.append(os.path.join(self.dirName, fileName))
        if len(result) < self.backupCount:
            result = []
        else:
            result.sort()
            result = result[:len(result) - self.backupCount]
        return result

    def _open(self):
        filename = '{}/{}.{}'.format(self.dirName, self.date.strftime(self.suffix), self.baseName)
        if self.encoding is None:
            stream = open(filename, self.mode)
        else:
            stream = codecs.open(filename, self.mode, self.encoding)
        if os.path.exists(self.baseFilename):
            try:
                os.remove(self.baseFilename)
            except OSError:
                pass
        try:
            os.symlink(filename, self.baseFilename)
        except OSError:
            pass
        return stream


def setup_log():
    '''配置日志'''
    if not os.path.exists('./logs'):
        os.mkdir('./logs')
    logging.basicConfig(level=Config.LOG_LEVEL, datefmt='%Y-%m-%d %H:%M:%S')
    # file_log_handler = RotatingFileHandler('logs/log', maxBytes=1024 * 1024 * 100, backupCount=10, encoding='UTF-8')
    file_log_handler = MidnightRotatingFileHandler('logs/log', backupCount=2, encoding='UTF-8')
    # file_log_handler = TimedRotatingFileHandler('logs/log', when='d', backupCount=30, encoding='UTF-8')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s')
    file_log_handler.setFormatter(formatter)
    file_log_handler.setLevel(Config.LOG_LEVEL)
    logging.getLogger().addHandler(file_log_handler)
