

import datetime
from demo_text import db
from demo_text.controllers import taskmode_blue
from demo_text.models.models import User
from demo_text.utils.response import Response

@taskmode_blue.route('/taskss/test/', methods=['GET'])
def task_test():
    return Response.success()
