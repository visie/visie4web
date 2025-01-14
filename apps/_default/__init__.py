import os
import glob
import importlib
# check compatibility
import py4web

assert py4web.check_compatible("0.1.20190709.1")

# by importing controllers you expose the actions defined in it
from . import controllers
# by importing db you expose it to the _dashboard/dbadmin
from .models import db
# import the scheduler
from .tasks import scheduler


modules = glob.glob(__file__.replace('__init__.py', '*/controllers.py'))
for module in modules:
    app = os.path.split(os.path.split(module)[0])[1]
    if app != 'scaffold':
        importlib.import_module(f".{app}", __name__)

# optional parameters
__version__ = "0.0.0"
__author__ = "you <you@example.com>"
__license__ = "anything you want"
