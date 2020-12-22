from flask import jsonify


class StatusCode():
    OK = (200, u'操作成功')
    SERVERERR = (100001, u'服务异常')
    NODATA = (100002, u'无数据')
    DATAEXIST = (100003, u'数据已存在')
    DATAERR = (100004, u'数据错误')
    PARAMERR = (100005, u'参数错误')
    NETWORKERR = (100006, u'网络异常')
    ACCESSERR = (100007, u'权限错误')
    NOTLOGIN = (100008, u'没有登录')


class RetCode:
    OK = 200
    SERVERERR = 500
    DB_ERR = 4001
    NODATA = 4002
    DATA_EXIST = 4003
    DATA_ERR = 4004
    PARAM_ERR = 4005
    NETWORK_ERR = 4006
    ACCESS_ERR = 4007
    NOT_LOGIN = 4008


RetMsgMap = {
    RetCode.OK: u'成功',
    RetCode.SERVERERR: u'服务器错误',
    RetCode.DB_ERR: u'系统错误',
    RetCode.NODATA: u'无数据',
    RetCode.DATA_EXIST: u'数据已存在',
    RetCode.DATA_ERR: u'数据错误',
    RetCode.PARAM_ERR: u'参数错误',
    RetCode.NETWORK_ERR: u'网络异常',
    RetCode.ACCESS_ERR: u'权限错误',
    RetCode.NOT_LOGIN: u'没有登录',
}


class Response():
    @classmethod
    def success(cls, data=None, msg=None):
        '''
        success response when request processed

        :param data: data response to exact request
        '''
        res = {
            'code': StatusCode.OK[0],
            'msg': StatusCode.OK[1]
        }

        if msg is not None:
            res['msg'] = msg

        if data is not None:
            res['data'] = data

        return jsonify(res)

    @classmethod
    def error(cls, code=StatusCode.SERVERERR, msg=None, data=None):
        '''
        error response when request processed

        :param data: data response to exact request
        '''
        if not isinstance(code, tuple) or len(code) != 2:
            raise Exception('server error')

        res = {
            'code': code[0],
            'msg': code[1]
        }

        if msg is not None:
            res['msg'] = msg

        if data is not None:
            res['data'] = data

        return jsonify(res)

    @classmethod
    def not_found(cls):
        '''
        error response when request processed

        :param data: data response to exact request
        '''
        res = {
            'code': StatusCode.NODATA[0],
            'msg': StatusCode.NODATA[1]
        }

        return jsonify(res)

    @classmethod
    def server_error(cls):
        '''
        error response when server internal error occured

        :param data: data response to exact request
        '''
        res = {
            'code': StatusCode.SERVERERR[0],
            'msg': StatusCode.SERVERERR[1]
        }

        return jsonify(res)
