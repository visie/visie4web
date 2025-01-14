from py4web import abort, action, request
from py4web.utils.grid import Grid, GridClassStyleBulma
from py4web.utils.form import FormStyleBulma

from .settings import APP_NAME, TEMPLATE_FOLDER
from ..common import (T, db, flash, requires_membership, menu)


TABLES = db.tables
menu.set(APP_NAME, [1000, 'Super Admin', (APP_NAME, 'index'), 'superadmin', [
    [0, table, (APP_NAME, 'table', table), 'superadmin']
    for table in TABLES
    ]])


@action(f"{APP_NAME}/index")
@action.uses(f"{TEMPLATE_FOLDER}index.html", requires_membership('superadmin'), T, flash)
def index():
    return dict(tables=TABLES, T=T, menu=menu, app_name=APP_NAME)


@action(f"{APP_NAME}/table/<table>")
@action(f"{APP_NAME}/table/<table>/<path:path>")
@action.uses(f"{TEMPLATE_FOLDER}table.html", requires_membership('superadmin'), T, flash)
def table(table, path=None):
    if table not in TABLES:
        abort(404)
    grid = Grid(
        path,
        query=(db[table].id>0),
        formstyle=FormStyleBulma,
        grid_class_style=GridClassStyleBulma,
    )
    return dict(table=table, grid=grid, T=T, menu=menu, app_name=APP_NAME)
