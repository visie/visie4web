import os

from ..settings import *

APP_FOLDER = os.path.dirname(__file__)
APP_NAME = os.path.split(APP_FOLDER)[-1]
TEMPLATE_FOLDER = f'../{APP_NAME}/templates/'

