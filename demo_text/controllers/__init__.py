import os

from flask import Blueprint

path = os.getcwd()
taskmode_blue = Blueprint('taskmode_blue', __name__)

