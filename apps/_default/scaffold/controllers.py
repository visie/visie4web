from py4web import action
from .settings import APP_NAME, TEMPLATE_FOLDER
from ..common import (T, auth, flash, menu)

menu.set(APP_NAME, [0, "Minha Página", (APP_NAME, 'index',), '', []])


@action(f"{APP_NAME}/index")
@action.uses(f"{TEMPLATE_FOLDER}index.html", auth.user, T, flash)
def index():
    user = auth.get_user()
    return dict(user=user, menu=menu, T=T, app_name=APP_NAME)



