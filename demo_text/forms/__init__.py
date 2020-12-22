import json
import re

from flask import request, current_app
from flask_wtf import FlaskForm
from wtforms import Field
from wtforms.validators import StopValidation, ValidationError

from demo_text.exceptions import APIException
from demo_text.utils.response import StatusCode


class Form(FlaskForm):
    @classmethod
    def create_api_form(cls, obj=None):
        try:
            form = cls(formdata=request.form, obj=obj, meta={'csrf': False})
            form._obj = obj
            if not form.validate():
                errors = list(form.errors.values())
                raise APIException(
                    errors[0][0], error_code=StatusCode.PARAMERR[0], status_code=200)
        except StopValidation as e:
            current_app.logger.error(e)
            raise APIException(
                str(e), error_code=StatusCode.PARAMERR[0], status_code=200)

        return form.data_format() if hasattr(form, 'data_format') else form.data

    def _validate_obj(self, key, value):
        obj = getattr(self, '_obj', None)
        return obj and getattr(obj, key) == value


class ListField(Field):
    def process_formdata(self, valuelist):
        try:
            if isinstance(valuelist, list):
                self.data = valuelist
            else:
                raise StopValidation('参数格式错误')
        except Exception as e:
            current_app.logger.error(e)
            raise StopValidation('参数格式错误')


class PermissionsField(Field):
    def process_formdata(self, value):
        '''the topic permissions authorized field
        format:
            string({product_id}-{topic_id}-{permission}#{product_id}-{topic_id}-{permission})
        example:
            '1-2-2#3-2-1'
        '''
        try:
            if not value or len(value) <= 0:
                raise StopValidation('参数格式错误')

            regex = re.compile(r'^\d+\-\d+\-[123]$')

            valuelist = value[0].split('#')
            permissions = []
            for p_str in valuelist:
                if not regex.match(p_str):
                    raise StopValidation('参数格式错误')
                permission = p_str.split('-')
                permissions.append([int(permission[0]), int(
                    permission[1]), int(permission[2])])
            self.data = permissions
        except Exception as e:
            current_app.logger.error(e)
            raise StopValidation('参数格式错误')


class JsonField(object):
    def __init__(self, message=None):
        self.message = message

    def json_validation(self, value):
        try:
            if not isinstance(value, str):
                raise StopValidation('参数格式错误')
            value_dict = json.loads(value)
            if not isinstance(value_dict, dict):
                raise StopValidation('参数格式错误')
            if len(value_dict.keys()) <= 0:
                raise StopValidation('参数格式错误')
        except Exception as e:
            current_app.logger.error(e)
            raise StopValidation('参数格式错误')

    def __call__(self, form, field):
        message = self.message
        if message is None:
            message = field.gettext('Invalid Json.')
        try:
            self.json_validation(field.data)
        except Exception as e:
            current_app.logger.error(e)
            raise ValidationError(message)
