
import datetime

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, SignatureExpired, BadSignature
from sqlalchemy import Column, String, TIMESTAMP, Text, text, UnicodeText
from sqlalchemy.dialects.mysql import INTEGER, TINYINT, MEDIUMTEXT

from demo_text import db
from settings import Config


class BaseMixin(object):
    def __getitem__(self, key):
        return getattr(self, key)


class TimestampMixin(object):
    createat = Column(TIMESTAMP, nullable=False, server_default=text(
        'CURRENT_TIMESTAMP'), comment='添加时间')
    updateat = Column(TIMESTAMP, nullable=False, server_default=text(
        'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='更新时间')

    @property
    def created_time(self):
        return self.createat.strftime('%Y-%m-%d %H:%M:%S')

    @property
    def updated_time(self):
        return self.updateat.strftime('%Y-%m-%d %H:%M:%S')


class Base(db.Model, BaseMixin):
    __abstract__ = True


class User(db.Model):
    '''用户信息表'''
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    # 用户名
    username = db.Column(db.String(255), unique=True, index=True, nullable=False)
    # 密码
    pwd = db.Column(db.String(255), index=True, nullable=False)

    def generate_user_token(self, expiration=Config.EXPIRATION):
        s = Serializer(Config.SECRET_KEY, expires_in=expiration)
        return s.dumps({'id': self.id, 'username': self.username}).decode('utf-8')

    @staticmethod
    def verify_user_token(token):
        s = Serializer(Config.SECRET_KEY, expires_in=Config.EXPIRATION)
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None  # valid token, but expired
        except BadSignature:
            return None  # invalid token
        user = User.query.get(data['id'])
        return user


class Car(Base):
    '''车辆信息表'''
    __tablename__ = 'car'

    id = Column(INTEGER(11), primary_key=True)
    carnum = Column(String(15), nullable=False, comment='车辆编号')
    cartype = Column(TINYINT(3), nullable=False, server_default=text("'1'"), comment='车辆类型（1清扫车）')
    carstu = Column(TINYINT(3), nullable=False, server_default=text("'2'"), comment='车辆状态（1在线，2离线，3任务中）')
    deviceid = Column(INTEGER(11), nullable=False, comment='设备id')
    devicekey = Column(String(64), nullable=False, comment='车辆key')
    devicesecret = Column(String(128), nullable=False, comment='车辆密钥')
    productkey = Column(String(64), nullable=False, comment='产品key')
    cardel = Column(TINYINT(3), nullable=False, server_default=text("'1'"), comment='1正常，2删除')
    createat = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    updateat = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'),
                      comment='更新时间')
    is_linked = db.Column(db.SmallInteger, server_default=text("'0'"),
                          nullable=False, comment='是否链接过')
    # 连接状态 0:未连接 1：已连接
    is_conn = db.Column(TINYINT(3), server_default=text("'0'"),
                        nullable=False, comment='连接状态')
    carmileage = db.Column(INTEGER(11), server_default=text("'0'"),
                           nullable=False, comment='总任务里程数')
    caratime = db.Column(INTEGER(11), server_default=text("'0'"),
                         nullable=False, comment='总任务时长')
    control = db.Column(INTEGER(11), server_default=text("'0'"),
                        nullable=False, comment='总任务时长')
    car_width = db.Column(INTEGER(11), server_default=text("150"),
                          nullable=False, comment='车辆清扫宽度cm')
    isonlineat = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    is_peo_start = Column(TINYINT(3), nullable=False, server_default=text("'1'"))
    is_conn_server = Column(TINYINT(3), nullable=False, server_default=text("'0'"))

    def to_dict(self):
        return {
            'id': self.id,
            'carnum': self.carnum,
            'cartype': self.cartype,
            'carstu': self.carstu,
            'deviceid': self.deviceid,
            'devicekey': self.devicekey,
            'devicesecret': self.devicesecret,
            'productkey': self.productkey,
            'deviceaddtime': self.deviceaddtime,
            'createat': self.created_time,
            'updateat': self.updated_time,
        }


class PlatformInfo(db.Model):
    __tablename__ = 'platform_info'
    id = db.Column(db.Integer, primary_key=True, comment='台架id')
    platform_name = db.Column(db.String(20), unique=True, nullable=False,
                              comment='台架名称')
    # 台架状态
    platform_status = db.Column(TINYINT(3), server_default=text("'0'"),
                                nullable=False, comment='台架状态')
    # 连接状态 0:未连接 1：已连接
    is_conn = db.Column(TINYINT(3), server_default=text("'0'"),
                        nullable=False, comment='连接状态')
    product_key = db.Column(db.String(64), nullable=False,
                            comment='product_key')
    device_key = db.Column(db.String(64), nullable=False, comment='device_key')
    device_secret = db.Column(db.String(128), nullable=False,
                              comment='device_secret')
    device_id = db.Column(db.Integer, nullable=False, comment='device_id')
    platdel = db.Column(TINYINT(3), nullable=False, server_default=text('"1"'))
    create_at = db.Column(db.DateTime,
                          server_default=text('CURRENT_TIMESTAMP'),
                          nullable=False, comment='创建时间')
    update_at = db.Column(db.DateTime, server_default=text(
        'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'),
                          nullable=False, comment='更新时间')


class ConnectDevice(db.Model):
    __tablename__ = 'conn_info'
    id = db.Column(db.Integer, primary_key=True, comment='车辆id')
    car_id = db.Column(db.Integer, index=True, nullable=False, comment='车辆id')
    plat_id = db.Column(db.Integer, index=True, nullable=False, comment='台架id')
    conn_status = db.Column(TINYINT(3), server_default=text("'0'"),
                            nullable=False, comment='连接状态')
    create_at = db.Column(db.DateTime,
                          server_default=text('CURRENT_TIMESTAMP'),
                          nullable=False, comment='连接时间')
    begin_time = db.Column(TIMESTAMP, nullable=False, comment='开始时间')
    end_time = db.Column(TIMESTAMP, nullable=False, comment='结束时间')
    type = db.Column(TINYINT(3), nullable=False, comment='类型（1、单独远程，2、自动任务下远程）')


class DataServerConfig(db.Model):
    __tablename__ = 'data_server_config'
    id = db.Column(db.Integer, primary_key=True, comment='id')
    data_server_ip_port = db.Column(db.String(30), nullable=False, comment='数据server的ip:port')
    create_at = db.Column(db.DateTime, server_default=text('CURRENT_TIMESTAMP'), nullable=False,
                          comment='创建时间')
    update_at = db.Column(db.DateTime, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')
                          , nullable=False, comment='更新时间')

    def to_dict(self):
        return {
            'id': self.id,
            'data_server_ip_port': self.data_server_ip_port,
            'create_at': self.create_at.strftime('%Y-%m-%d %H:%M:%S'),
            'update_at': self.update_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class UserBase(db.Model):
    __abstract__ = True

    def generate_user_token(self, expiration=Config.APP_EXPIRATION):
        secret_key = Config.SECRET_KEY if self.__class__.__name__ == 'UserInfo' else Config.SECRET_KEY + 'for_service'
        s = Serializer(secret_key, expires_in=expiration)
        return s.dumps({'id': self.id, 'user_name': self.user_name}).decode(
            'utf-8')

    @staticmethod
    def verify_user_token(token, is_service_user=False):
        secret_key = Config.SECRET_KEY if not is_service_user \
            else Config.SECRET_KEY + 'for_service'
        s = Serializer(secret_key)
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None  # valid token, but expired
        except BadSignature:
            return None  # invalid token

        if is_service_user:
            user = db.session.query(ServiceUserInfo).filter(
                ServiceUserInfo.id == data['id']
            ).first()
            if user and user.user_name == data['user_name']:
                return user
        return None  # maybe for service


class ServiceUserInfo(UserBase):
    __tablename__ = 'service_user_info'
    id = db.Column(db.Integer, primary_key=True, comment='用户id')
    user_name = db.Column(db.String(32), index=True, nullable=False,
                          comment='用户名')
    # 用户账号（手机号）
    user_cell = db.Column(db.String(12), unique=True, nullable=False,
                          comment='用户账号（手机号）')
    passwd = db.Column(db.String(32), nullable=False, comment='密码')
    create_at = db.Column(db.DateTime,
                          server_default=text('CURRENT_TIMESTAMP'),
                          nullable=False, comment='创建时间')
    update_at = db.Column(db.DateTime, server_default=text(
        'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'),
                          nullable=False, comment='更新时间')

    def to_dict(self):
        return {
            'user_id': self.id,
            'user_name': self.user_name,
            'user_cell': self.user_cell,
            'create_at': datetime.datetime.strftime(self.create_at,
                                                    '%Y-%m-%d %H:%M:%S')
        }


class CarType(Base):
    '''车辆类型信息表'''
    __tablename__ = 'cartype'

    id = Column(INTEGER(11), primary_key=True)
    cartype = Column(TINYINT(1), nullable=False, server_default=text('"1"'), comment='车辆类型（1清扫车）')
    typename = Column(String(128), nullable=False, comment='车辆类型名称')

    def to_dict(self):
        return {
            'id': self.id,
            'cartype': self.cartype,
            'typename': self.typename,
        }


class Map(Base, TimestampMixin):
    '''高精度地图信息表'''
    __tablename__ = 'map'

    id = Column(INTEGER(11), primary_key=True)
    mapname = Column(String(50), nullable=False, comment='高精度度地图名称')
    operationid = Column(INTEGER(11), nullable=False, comment='所属作业区域id')
    mapdetails = Column(String(200), nullable=False, server_default=text('""'), comment='地图描述')
    maptxturl = Column(String(128), nullable=False, comment='高精度地图文件url')
    txtname = Column(String(128), nullable=False, comment='原地图文件名称')
    latlgs = Column(MEDIUMTEXT, nullable=False, comment='坐标点集')
    mapdel = Column(TINYINT(1), nullable=False, server_default=text('"1"'), comment='1正常，2删除')
    createat = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    updateat = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'),
                      comment='更新时间')

    def to_dict(self):
        return {
            # 'id': self.id,
            'mapname': self.mapname,
            'operationid': self.operationid,
            'mapdetails': self.mapdetails,
            'maptxturl': self.maptxturl,
            'txtname': self.txtname,
            'latlgs': self.latlgs,
            # 'createat': self.created_time,
            # 'updateat': self.updated_time,
        }


class Operation(Base, TimestampMixin):
    '''作业区域信息表'''
    __tablename__ = 'operation'

    id = Column(INTEGER(11), primary_key=True)
    operationname = Column(String(40), nullable=False, comment='作业区域名称')
    latlgs = Column(db.Text, nullable=False, comment='坐标点集')
    coordinate = Column(String(100), nullable=False, comment='中心点坐标')
    mapgrade = Column(INTEGER(11), nullable=False, comment='地图比例')
    operationdel = Column(TINYINT(1), nullable=False, server_default=text('"1"'), comment='1正常，2删除')
    createat = Column(TIMESTAMP, nullable=False, server_default=text(
        'CURRENT_TIMESTAMP'), comment='创建时间')

    def to_dict(self):
        return {
            'id': self.id,
            'operationname': self.operationname,
            'latlgs': self.latlgs,
            'coordinate': self.coordinate,
            'mapgrade': self.mapgrade,
            'createat': self.created_time,
            'updateat': self.updated_time,
        }


class Taskbase(Base, TimestampMixin):
    '''任务基础信息表'''
    __tablename__ = 'taskbase'

    id = Column(INTEGER(11), primary_key=True)
    taskname = Column(String(30), nullable=False, comment='任务名称')
    operationid = Column(INTEGER(11), nullable=False, comment='作业区域id')
    mapid = Column(INTEGER(11), nullable=False, comment='高精度地图id')
    carid = Column(INTEGER(11), nullable=False, server_default=text('"0"'), comment='指派车辆id')
    carnum = Column(String(15), nullable=False, server_default=text('""'), comment='车辆编号')
    taskbegintime = Column(String(64), nullable=False, comment='开始时间')
    taskfrequency = Column(TINYINT(3), nullable=False, server_default=text('"2"'), comment='任务频率(1每日, 2单次)')
    taskstu = Column(TINYINT(3), nullable=False, server_default=text('"0"'), comment='任务状态(0未指派，1执行中，2已停止)')
    lighting = Column(TINYINT(3), nullable=False, server_default=text('"0"'), comment='作业灯光(0关闭，1打开)')
    music = Column(TINYINT(3), nullable=False, server_default=text('"0"'), comment='作业音乐(0关闭，1打开)')
    pattern = Column(TINYINT(3), nullable=False, server_default=text('"0"'), comment='作业模式(0干式清扫，1干湿两用)')
    cyclenumber = Column(TINYINT(3), nullable=False, server_default=text('"1"'), comment='工作圈数(1一圈，2两圈)')
    tasktxt = Column(String(150), nullable=False, server_default=text('""'), comment='任务描述')
    createat = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    isdel = Column(TINYINT(3), nullable=False, server_default=text('"0"'), comment='循环任务软删除0、正常，1、删除')

    def to_dict(self):
        resp_dict = {
            # 'id': self.id,
            'taskname': self.taskname,
            'operationid': self.operationid,
            'mapid': self.mapid,
            # 'carid': self.carid,
            # 'carnum': self.carnum,
            'taskbegintime': self.taskbegintime,
            'taskfrequency': self.taskfrequency,
            # 'taskstu': self.taskstu,
            'lighting': self.lighting,
            'music': self.music,
            'pattern': self.pattern,
            'cyclenumber': self.cyclenumber,
            'tasktxt': self.tasktxt,
            # 'createat': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            # 'updateat': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        }
        return resp_dict


class Taskdetail(Base):
    '''任务详情表'''
    __tablename__ = 'taskdetail'

    id = Column(INTEGER(11), primary_key=True)
    taskid = Column(INTEGER(11), nullable=False, comment='任务名称')
    carid = Column(INTEGER(11), nullable=False, server_default=text('"0"'), comment='指派车辆id')
    carnum = Column(String(15), nullable=False, server_default=text('""'), comment='车辆编号')
    taskstu = Column(TINYINT(1), nullable=False, server_default=text('"0"'),
                     comment='任务状态 (0未指派，1已超时，2未执行，3任务中，4任务中断，5已完成)')
    taskbegintime = Column(TIMESTAMP, nullable=False, comment='任务开始时间')
    begintime = Column(TIMESTAMP, nullable=False, comment='开始任务时间')
    endtime = Column(TIMESTAMP, nullable=False, server_default=text('""'), comment='结束任务时间')
    taskfrequency = Column(TINYINT(3), nullable=False, server_default=text('"1"'), comment='任务频率(1每日, 2单次)')
    createat = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')

    def to_dict(self):
        resp_dict = {
            'id': self.id,
            'taskid': self.taskid,
            'carid': self.carid,
            'carnum': self.carnum,
            'taskstu': self.taskstu,
            'begintime': self.begintime,
            'endtime': self.endtime,
            'taskfrequency': self.taskfrequency,
            'createat': self.createat.strftime('%Y-%m-%d %H:%M:%S'),
        }
        return resp_dict


class CarEveryday(Base):
    '''车辆每日工作信息表'''
    __tablename__ = 'car_everyday'

    id = Column(INTEGER(11), primary_key=True)
    car_id = Column(INTEGER(11), nullable=False, comment='carid')
    data = Column(TIMESTAMP, nullable=True, comment='日期')
    atime = Column(INTEGER(11), nullable=False, server_default=text('0'), comment='时长')
    datatime = Column(INTEGER(11), nullable=False, server_default=text('0'), comment='今日哦o点时间戳')
    mileage = Column(INTEGER(11), nullable=False, server_default=text('0'), comment='里程数')

    def to_dict(self):
        resp_dict = {
            'id': self.id,
            'car_id': self.car_id,
            'data': self.data,
            'atime': self.atime,
            'mileage': self.mileage,
        }
        return resp_dict
