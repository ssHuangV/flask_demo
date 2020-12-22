
from flask import request
from wtforms import StringField, IntegerField

from wtforms.validators import DataRequired, StopValidation, Length, Regexp, Optional, AnyOf
from demo_text import db
from demo_text.models.models import Taskbase, Taskdetail
from . import Form


class TaskAddForm(Form):
    """
    task add Form
    rules:
    """
    # 地图名称
    taskname = StringField(validators=[
        DataRequired(message='任务名称'),
        Length(min=1, max=20, message='请输入1~20位字符'),
        # Regexp(
        #     regex="^[\u4e00-\u9fa5a-zA-Z0-9_]{3,7}",
        #     message='驾驶舱编号由3-7位中英文数字组成')
        # Regexp(regex='^1[0123456789]\d{9}$',
        #        message='手机号码不合法')
        # Regexp(
        #     regex="^[\u4e00-\u9fa5_a-zA-Z0-9]+$",
        #     message='任务名称支持文字、英文和数字')
    ])

    def validate_taskname(self, field):
        application = db.session.query(Taskbase).filter(
            Taskbase.taskname == field.data).first()
        if application is not None:
            raise StopValidation('任务名称已存在，请勿重复添加！')

