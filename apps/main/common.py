"""
This file defines cache, session, and translator T object for the app
These are fixtures that every app needs so probably you will not be editing this file
"""
import os
import sys

from pydal.tools.scheduler import Scheduler
from pydal.tools.tags import Tags

from py4web import DAL, Cache, Field, Flash, Session, Translator, HTTP, action, URL
from py4web.core import Fixture
from py4web.server_adapters.logging_utils import make_logger
from py4web.utils.auth import Auth
from py4web.utils.downloader import downloader
from py4web.utils.factories import ActionFactory
from py4web.utils.mailer import Mailer
from py4web.utils.form import FormStyleBulma
from pydal.tools.tags import Tags
from yatl import A, DIV, CAT

from . import settings

# #######################################################
# implement custom loggers form settings.LOGGERS
# #######################################################
logger = make_logger("py4web:" + settings.APP_NAME, settings.LOGGERS)

# #######################################################
# connect to db
# #######################################################
db = DAL(
    settings.DB_URI,
    folder=settings.DB_FOLDER,
    pool_size=settings.DB_POOL_SIZE,
    migrate=settings.DB_MIGRATE,
    fake_migrate=settings.DB_FAKE_MIGRATE,
)

# #######################################################
# define global objects that may or may not be used by the actions
# #######################################################
cache = Cache(size=1000)
T = Translator(settings.T_FOLDER)

# #######################################################
# pick the session type that suits you best
# #######################################################
if settings.SESSION_TYPE == "cookies":
    session = Session(secret=settings.SESSION_SECRET_KEY, name='session')

elif settings.SESSION_TYPE == "redis":
    import redis

    host, port = settings.REDIS_SERVER.split(":")
    # for more options: https://github.com/andymccurdy/redis-py/blob/master/redis/client.py
    conn = redis.Redis(host=host, port=int(port))
    conn.set = (
        lambda k, v, e, cs=conn.set, ct=conn.ttl: cs(k, v, ct(k))
        if ct(k) >= 0
        else cs(k, v, e)
    )
    session = Session(secret=settings.SESSION_SECRET_KEY, storage=conn)

elif settings.SESSION_TYPE == "memcache":
    import time

    import memcache

    conn = memcache.Client(settings.MEMCACHE_CLIENTS, debug=0)
    session = Session(secret=settings.SESSION_SECRET_KEY, storage=conn)

elif settings.SESSION_TYPE == "database":
    from py4web.utils.dbstore import DBStore

    session = Session(secret=settings.SESSION_SECRET_KEY, storage=DBStore(db))

# #######################################################
# Instantiate the object and actions that handle auth
# #######################################################
auth = Auth(session, db, define_tables=False)
auth.use_username = False
auth.param.registration_requires_confirmation = settings.VERIFY_EMAIL
auth.param.registration_requires_approval = settings.REQUIRES_APPROVAL
auth.param.login_after_registration = settings.LOGIN_AFTER_REGISTRATION
auth.param.allowed_actions = settings.ALLOWED_ACTIONS
auth.param.login_expiration_time = 3600
auth.param.password_complexity = {"entropy": settings.PASSWORD_ENTROPY}
auth.param.block_previous_password_num = 3
auth.param.default_login_enabled = settings.DEFAULT_LOGIN_ENABLED
auth.param.formstyle=FormStyleBulma
auth.param.button_classes = {k:v+" button ml-3" for k,v in auth.param.button_classes.items()}
auth.define_tables()

flash = auth.flash

# #######################################################
# Configure email sender for auth
# #######################################################
if settings.SMTP_SERVER:
    auth.sender = Mailer(
        server=settings.SMTP_SERVER,
        sender=settings.SMTP_SENDER,
        login=settings.SMTP_LOGIN,
        tls=settings.SMTP_TLS,
        ssl=settings.SMTP_SSL,
    )

# #######################################################
# Create a table to tag users as group members
# #######################################################
if auth.db:
    groups = Tags(db.auth_user, "groups")

# #######################################################
# Enable optional auth plugin
# #######################################################
if settings.USE_PAM:
    from py4web.utils.auth_plugins.pam_plugin import PamPlugin

    auth.register_plugin(PamPlugin())

if settings.USE_LDAP:
    from py4web.utils.auth_plugins.ldap_plugin import LDAPPlugin

    auth.register_plugin(LDAPPlugin(db=db, groups=groups, **settings.LDAP_SETTINGS))

if settings.OAUTH2GOOGLE_CLIENT_ID:
    from py4web.utils.auth_plugins.oauth2google import OAuth2Google  # TESTED

    auth.register_plugin(
        OAuth2Google(
            client_id=settings.OAUTH2GOOGLE_CLIENT_ID,
            client_secret=settings.OAUTH2GOOGLE_CLIENT_SECRET,
            callback_url="auth/plugin/oauth2google/callback",
        )
    )

if settings.OAUTH2GOOGLE_SCOPED_CREDENTIALS_FILE:
    from py4web.utils.auth_plugins.oauth2google_scoped import \
        OAuth2GoogleScoped  # TESTED

    auth.register_plugin(
        OAuth2GoogleScoped(
            secrets_file=settings.OAUTH2GOOGLE_SCOPED_CREDENTIALS_FILE,
            scopes=[],  # Put here any scopes you want in addition to login
            db=db,  # Needed to store credentials in auth_credentials
        )
    )

if settings.OAUTH2GITHUB_CLIENT_ID:
    from py4web.utils.auth_plugins.oauth2github import OAuth2Github  # TESTED

    auth.register_plugin(
        OAuth2Github(
            client_id=settings.OAUTH2GITHUB_CLIENT_ID,
            client_secret=settings.OAUTH2GITHUB_CLIENT_SECRET,
            callback_url="auth/plugin/oauth2github/callback",
        )
    )

if settings.OAUTH2FACEBOOK_CLIENT_ID:
    from py4web.utils.auth_plugins.oauth2facebook import \
        OAuth2Facebook  # UNTESTED

    auth.register_plugin(
        OAuth2Facebook(
            client_id=settings.OAUTH2FACEBOOK_CLIENT_ID,
            client_secret=settings.OAUTH2FACEBOOK_CLIENT_SECRET,
            callback_url="auth/plugin/oauth2facebook/callback",
        )
    )

if settings.OAUTH2OKTA_CLIENT_ID:
    from py4web.utils.auth_plugins.oauth2okta import OAuth2Okta  # TESTED

    auth.register_plugin(
        OAuth2Okta(
            client_id=settings.OAUTH2OKTA_CLIENT_ID,
            client_secret=settings.OAUTH2OKTA_CLIENT_SECRET,
            callback_url="auth/plugin/oauth2okta/callback",
        )
    )


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

# #######################################################
# Define convenience decorators
# They can be used instead of @action and @action.uses
# They should NEVER BE MIXED with @action and @action.uses
# If you need to provide extra fixtures for a specific controller
# add them like this: @authenticated(uses=[extra_fixture])
# #######################################################
unauthenticated = ActionFactory(db, session, T, flash, auth)
authenticated = ActionFactory(db, session, T, flash, auth.user)


class Menu:
    def __init__(self):
        self.menu_items = {}
    def set(self, name, item):
        self.menu_items[name] = item
    def render(self, user_id):
        u_groups = groups.get(user_id)
        return CAT(*[self.build_item(item, u_groups) for item in sorted(self.menu_items.values())])
    def build_item(self, item, u_groups):
        if item[3] and not item[3] in u_groups:
            return ''
        if item[4]:
            pass
        else:
            return A(item[1], _href=URL(*item[2], use_appname=False), _class="navbar-item")


menu = Menu()


class requires_membership(Fixture):
    def __init__(self, group):
        self.__prerequisites__ = [auth.user]
        self.group  = group
    def on_request(self, context):
        user_id = auth.get_user()['id']
        if self.group not in groups.get(user_id):
            raise HTTP(401)

