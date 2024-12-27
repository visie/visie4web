"""
This file defines cache, session, and translator T object for the app
These are fixtures that every app needs so probably you will not be editing this file
"""
import os
import sys

from pydal.tools.scheduler import Scheduler
from pydal.tools.tags import Tags

from py4web import DAL, Cache, Field, Flash, Session, Translator, action
from py4web.server_adapters.logging_utils import make_logger
from py4web.utils.downloader import downloader
from py4web.utils.factories import ActionFactory
from py4web.utils.mailer import Mailer

from . import settings
from ..main.common import db, auth, flash, groups, session, unauthenticated, authenticated, requires_membership, menu

# #######################################################
# implement custom loggers form settings.LOGGERS
# #######################################################
logger = make_logger("py4web:" + settings.APP_NAME, settings.LOGGERS)


# #######################################################
# define global objects that may or may not be used by the actions
# #######################################################
cache = Cache(size=1000)
T = Translator(settings.T_FOLDER)


# #######################################################
# Define a convenience action to allow users to download
# files uploaded and reference by Field(type='upload')
# #######################################################
if settings.UPLOAD_FOLDER:

    @action("download/<filename>")
    @action.uses(db)
    def download(filename):
        return downloader(db, settings.UPLOAD_FOLDER, filename)

    # To take advantage of this in Form(s)
    # for every field of type upload you MUST specify:
    #
    # field.upload_path = settings.UPLOAD_FOLDER
    # field.download_url = lambda filename: URL('download/%s' % filename)

# #######################################################
# Define and optionally start the scheduler
# #######################################################
if settings.USE_SCHEDULER:
    scheduler = Scheduler(
        db, logger=logger, max_concurrent_runs=settings.SCHEDULER_MAX_CONCURRENT_RUNS
    )
    scheduler.start()
else:
    scheduler = None
