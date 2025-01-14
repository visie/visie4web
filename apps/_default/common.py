from pydal.tools.scheduler import Scheduler
from pydal.tools.tags import Tags

from py4web.core import Fixture
from py4web import DAL, Cache, Field, Flash, Session, Translator, action, HTTP, URL
from py4web.server_adapters.logging_utils import make_logger
from py4web.utils.auth import Auth
from py4web.utils.downloader import downloader
from py4web.utils.factories import ActionFactory
from py4web.utils.mailer import Mailer
from py4web.utils.form import FormStyleBulma

from yatl import A, CAT

from . import settings

logger = make_logger("py4web:" + settings.APP_NAME, settings.LOGGERS)

db = DAL(
    settings.DB_URI,
    folder=settings.DB_FOLDER,
    pool_size=settings.DB_POOL_SIZE,
    migrate=settings.DB_MIGRATE,
    fake_migrate=settings.DB_FAKE_MIGRATE,
)


cache = Cache(size=1000)
T = Translator(settings.T_FOLDER)


if settings.SESSION_TYPE == "cookies":
    session = Session(secret=settings.SESSION_SECRET_KEY)

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
    import memcache

    conn = memcache.Client(settings.MEMCACHE_CLIENTS, debug=0)
    session = Session(secret=settings.SESSION_SECRET_KEY, storage=conn)

elif settings.SESSION_TYPE == "database":
    from py4web.utils.dbstore import DBStore

    session = Session(secret=settings.SESSION_SECRET_KEY, storage=DBStore(db))


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
auth.fix_actions()

flash = auth.flash


if settings.SMTP_SERVER:
    auth.sender = Mailer(
        server=settings.SMTP_SERVER,
        sender=settings.SMTP_SENDER,
        login=settings.SMTP_LOGIN,
        tls=settings.SMTP_TLS,
        ssl=settings.SMTP_SSL,
    )

if auth.db:
    groups = Tags(db.auth_user, "groups")

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


if settings.UPLOAD_FOLDER:
    @action("download/<filename>")
    @action.uses(db)
    def download(filename):
        return downloader(db, settings.UPLOAD_FOLDER, filename)


if settings.USE_SCHEDULER:
    scheduler = Scheduler(
        db, logger=logger, max_concurrent_runs=settings.SCHEDULER_MAX_CONCURRENT_RUNS
    )
    scheduler.start()
else:
    scheduler = None


auth.enable(uses=(session, T, db), env=dict(T=T))
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
        if item[3] and item[3] not in u_groups:
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

