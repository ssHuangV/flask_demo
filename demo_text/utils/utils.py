
import datetime
import hashlib
import json
import random
import time
from functools import wraps
from threading import Lock
from uuid import uuid4

import math
from apscheduler.triggers.date import DateTrigger
from flask import g
from flask import request, jsonify, current_app
from sqlalchemy import or_

from demo_text import db
from demo_text import redis_store
from demo_text.models.models import User, ServiceUserInfo
from demo_text.utils.response import RetCode, RetMsgMap
from manage import scheduler
from settings import Config

lock = Lock()


# 移除
def remove_task(id):
    try:
        scheduler.delete_job(id)
    except Exception as e:
        current_app.logger.error(e)
        return 0
    return 1


# 添加
def add_timing_task(task, id, run_date, args):
    try:
        trigger = DateTrigger(run_date=run_date)
        scheduler.add_job(func=task, id=id, trigger=trigger, args=args, jobstore='redis', replace_existing=True)
    except Exception as e:
        current_app.logger.error(e)
        return 0
    return 1


# 获取
def get_task(id):
    job = scheduler.get_job(id)
    return job


# 获取全部
def get_tasks():
    jobs = scheduler.get_jobs()
    return jobs


uuid_chars = ('a', 'b', 'c', 'd', 'e', 'f',
              'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's',
              't', 'u', 'v', 'w', 'x', 'y', 'z', '0', '1', '2', '3', '4', '5',
              '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I',
              'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V',
              'W', 'X', 'Y', 'Z')


def get_request_id():
    result = ''
    for i in range(4):
        uuid = str(uuid4()).replace('-', '')
        for i in range(8):
            sub = uuid[i * 4: i * 4 + 4]
            x = int(sub, 16)
            result += uuid_chars[x % 0x3E]
    return result


def get_centerpoint(dots):
    '''
    根据坐标集确定一个中心点
    :param dots:
    :return:
    '''
    area = 0
    cp_lng, cp_lat = 0, 0
    try:
        for i in range(len(dots)):
            lng = float(dots[i][0])  # 经度
            lat = float(dots[i][1])  # 纬度
            if i == 0:
                lng1 = float(dots[-1][0])
                lat1 = float(dots[-1][1])
            else:
                lng1 = float(dots[i - 1][0])
                lat1 = float(dots[i - 1][1])
            fg = (lat * lng1 - lng * lat1) / 2.0
            area += fg
            cp_lat += fg * (lat + lat1) / 3.0
            cp_lng += fg * (lng + lng1) / 3.0
        cp_lat = cp_lat / area
        cp_lng = cp_lng / area
    except Exception as e:
        current_app.logger.error(e)
        return False

    return {'longitude': cp_lng, 'latitude': cp_lat}


def is_login(can_app_use=False):
    """检验登录状态"""

    def check_user_auth(func):
        @wraps(func)
        def check_login(*args, **kwargs):
            token = request.headers.get("speepertoken")
            if not token:
                return jsonify(code=RetCode.NOT_LOGIN,
                               msg=RetMsgMap.get(RetCode.NOT_LOGIN))

            user = User.verify_user_token(token=token)

            if not user and can_app_use:
                user = ServiceUserInfo.verify_user_token(token,
                                                         is_service_user=True)

            if not user:
                return jsonify(code=RetCode.NOT_LOGIN,
                               msg='未登录或当前用户权限不足')
            else:
                g.user = user
                return func(*args, **kwargs)

        return check_login

    return check_user_auth


def get_16_md5(s):
    return hashlib.md5(bytes(s, encoding="utf8")).hexdigest()[:16]


class RSExceptin(Exception):
    pass


class WGS84ToBD09(object):
    def __init__(self):
        self.x_pi = 3.14159265358979324 * 3000.0 / 180.0
        self.pi = 3.1415926535897932384626  # π
        self.a = 6378245.0  # 长半轴
        self.ee = 0.00669342162296594323  # 偏心率平方

    def gcj02_to_bd09(self, lng, lat):
        """
        火星坐标系(GCJ-02)转百度坐标系(BD-09)
        谷歌、高德——>百度
        :param lng:火星坐标经度
        :param lat:火星坐标纬度
        :return:
        """
        z = math.sqrt(lng * lng + lat * lat) + 0.00002 * math.sin(
            lat * self.x_pi)
        theta = math.atan2(lat, lng) + 0.000003 * math.cos(lng * self.x_pi)
        bd_lng = z * math.cos(theta) + 0.0065
        bd_lat = z * math.sin(theta) + 0.006
        return [bd_lng, bd_lat]

    def bd09_to_gcj02(self, bd_lon, bd_lat):
        """
        百度坐标系(BD-09)转火星坐标系(GCJ-02)
        百度——>谷歌、高德
        :param bd_lat:百度坐标纬度
        :param bd_lon:百度坐标经度
        :return:转换后的坐标列表形式
        """
        x = bd_lon - 0.0065
        y = bd_lat - 0.006
        z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * self.x_pi)
        theta = math.atan2(y, x) - 0.000003 * math.cos(x * self.x_pi)
        gg_lng = z * math.cos(theta)
        gg_lat = z * math.sin(theta)
        return [gg_lng, gg_lat]

    def gcj02_to_wgs84(self, lng, lat):
        """
        GCJ02(火星坐标系)转GPS84
        :param lng:火星坐标系的经度
        :param lat:火星坐标系纬度
        :return:
        """
        if self.out_of_china(lng, lat):
            return [lng, lat]
        dlat = self._transformlat(lng - 105.0, lat - 35.0)
        dlng = self._transformlng(lng - 105.0, lat - 35.0)
        radlat = lat / 180.0 * self.pi
        magic = math.sin(radlat)
        magic = 1 - self.ee * magic * magic
        sqrtmagic = math.sqrt(magic)
        dlat = (dlat * 180.0) / (
                (self.a * (1 - self.ee)) / (magic * sqrtmagic) * self.pi)
        dlng = (dlng * 180.0) / (
                self.a / sqrtmagic * math.cos(radlat) * self.pi)
        mglat = lat + dlat
        mglng = lng + dlng
        return [lng * 2 - mglng, lat * 2 - mglat]

    def wgs84_to_gcj02(self, lng, lat):
        """
        WGS84转GCJ02(火星坐标系)
        :param lng:WGS84坐标系的经度
        :param lat:WGS84坐标系的纬度
        :return:
        """
        if self.out_of_china(lng, lat):  # 判断是否在国内
            return [lng, lat]
        dlat = self._transformlat(lng - 105.0, lat - 35.0)
        dlng = self._transformlng(lng - 105.0, lat - 35.0)
        radlat = lat / 180.0 * self.pi
        magic = math.sin(radlat)
        magic = 1 - self.ee * magic * magic
        sqrtmagic = math.sqrt(magic)
        dlat = (dlat * 180.0) / (
                (self.a * (1 - self.ee)) / (magic * sqrtmagic) * self.pi)
        dlng = (dlng * 180.0) / (
                self.a / sqrtmagic * math.cos(radlat) * self.pi)
        mglat = lat + dlat
        mglng = lng + dlng
        return [mglng, mglat]

    def wgs84_to_bd09(self, lon, lat):
        lon, lat = self.wgs84_to_gcj02(lon, lat)
        return self.gcj02_to_bd09(lon, lat)

    def bd09_to_wgs84(self, bd_lon, bd_lat):
        lon, lat = self.bd09_to_gcj02(bd_lon, bd_lat)
        return self.gcj02_to_wgs84(lon, lat)

    def _transformlat(self, lng, lat):
        ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + \
              0.1 * lng * lat + 0.2 * math.sqrt(math.fabs(lng))
        ret += (20.0 * math.sin(6.0 * lng * self.pi) + 20.0 *
                math.sin(2.0 * lng * self.pi)) * 2.0 / 3.0
        ret += (20.0 * math.sin(lat * self.pi) + 40.0 *
                math.sin(lat / 3.0 * self.pi)) * 2.0 / 3.0
        ret += (160.0 * math.sin(lat / 12.0 * self.pi) + 320 *
                math.sin(lat * self.pi / 30.0)) * 2.0 / 3.0
        return ret

    def _transformlng(self, lng, lat):
        ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + \
              0.1 * lng * lat + 0.1 * math.sqrt(math.fabs(lng))
        ret += (20.0 * math.sin(6.0 * lng * self.pi) + 20.0 *
                math.sin(2.0 * lng * self.pi)) * 2.0 / 3.0
        ret += (20.0 * math.sin(lng * self.pi) + 40.0 *
                math.sin(lng / 3.0 * self.pi)) * 2.0 / 3.0
        ret += (150.0 * math.sin(lng / 12.0 * self.pi) + 300.0 *
                math.sin(lng / 30.0 * self.pi)) * 2.0 / 3.0
        return ret

    def out_of_china(self, lng, lat):
        """
        判断是否在国内，不在国内不做偏移
        :param lng:
        :param lat:
        :return:
        """
        return not (
                lng > 73.66 and lng < 135.05 and lat > 3.86 and lat < 53.55)


def random_one():
    uuid_chars = ("a", "b", "c", "d", "e", "f",
                  "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s",
                  "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5",
                  "6", "7", "8", "9", "A", "B", "C", "D", "E", "F", "G", "H", "I",
                  "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V",
                  "W", "X", "Y", "Z")

    n = random.randint(0, len(uuid_chars))
    car_name = str(time.time()).replace('.', '') + uuid_chars[n]
    return car_name[3:]


if __name__ == '__main__':
    pass
