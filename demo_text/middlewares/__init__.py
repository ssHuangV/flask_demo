import re

from flask import request, current_app

from demo_text.exceptions import APIException

class MiddlewareManger(object):
    '''
    中间件管理类
    '''

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        @app.before_request
        def pre_process():
            return self.before_request()

        @app.after_request
        def post_process(response):
            return self.after_request(response)

    def before_request(self):
        '''
        This call before the request to be processing
        '''
        # TODO 进行认证校验
        if request.method in ['GET', 'POST', 'PUT', 'DELETE']:
            pattern = re.compile('/api/')
            res = re.findall(pattern, request.path)
            # 验证激活
            if res and request.path not in ['/api/user/login/', '/api/login/app/']:

                try:
                    token = request.headers.get('speepertoken')
                    # if not token:
                    #     raise APIException(msg='没有登录', error_code=100008, status_code=200)
                    # user = User.verify_user_token(token)
                    # if not user:
                    #     raise APIException(msg='没有登录', error_code=100008, status_code=200)

                except Exception as e:
                    current_app.logger.error(e)
                    raise APIException(msg='没有登录', error_code=100008, status_code=200)
        return None

    def after_request(self, response):
        '''
        This call after the request to be processed
        '''
        # TODO 记录请求日志
        return response
