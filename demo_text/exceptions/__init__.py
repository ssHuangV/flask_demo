import sys
import traceback

from flask import jsonify, request, current_app
from werkzeug.exceptions import NotFound

from demo_text.utils.response import Response
from log import record_system_log


class APIException(Exception):
    status_code = 500
    msg = 'server missing...'
    error_code = 100001
    payload = None

    def __init__(self, msg=None, error_code=None, status_code=None, payload=None):
        Exception.__init__(self)
        if msg is not None:
            self.msg = msg

        if error_code is not None:
            self.error_code = error_code

        if status_code is not None:
            self.status_code = status_code

        if payload is not None:
            self.payload = payload

    def to_dict(self):
        resp = dict()
        if self.payload is not None:
            resp['data'] = dict(self.payload or ())
        resp['code'] = self.error_code
        resp['msg'] = self.msg
        return resp


def handle_exception(error):
    if isinstance(error, NotFound):
        resp = Response.not_found()
        resp.status_code = 404

    elif isinstance(error, APIException):
        resp = jsonify(error.to_dict())
        resp.status_code = error.status_code

    else:
        ex_type, ex_val, ex_stack = sys.exc_info()
        filename = ''
        lineno = ''
        for idx, stack in enumerate(traceback.extract_tb(ex_stack)):
            if idx == len(traceback.extract_tb(ex_stack)) - 1:
                filename = stack.filename
                lineno = stack.lineno
        params = {
            'type': 'handle_exceptions',
            'filename': filename,
            'lineno': lineno,
        }
        record_system_log(error, params, request=request)
        current_app.logger.error(error)
        resp = Response.server_error()
        resp.status_code = 200

    return resp
