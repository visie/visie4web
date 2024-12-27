from py4web import URL, abort, action, redirect, request
from py4web.utils.grid import Grid, GridClassStyleBulma
from py4web.utils.form import FormStyleBulma

from .common import (T, auth, authenticated, cache, db, flash, logger, session,
                     unauthenticated, requires_membership, menu)

menu.set('superadmin', [1000, 'Superadmin', ('superadmin', 'index'), 'superadmin', []])


@action("auth/<path:path>")
def auth_redirect(path):
    redirect(URL('account/auth', path, vars=request.query, use_appname=False))

@action("index")
@action.uses("index.html", requires_membership('superadmin'), T, flash)
def index():
    return dict(tables=db.tables, T=T, menu=menu)

@action("table/<table>")
@action("table/<table>/<path:path>")
@action.uses("table.html", requires_membership('superadmin'), T, flash)
def table(table, path=None):
    if table not in db.tables:
        abort(404)
    grid = Grid(
        path,
        query=(db[table].id>0),
        formstyle=FormStyleBulma,
        grid_class_style=GridClassStyleBulma,
    )
    return dict(table=table, grid=grid, T=T, menu=menu)
