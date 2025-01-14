from pydal.validators import IS_NOT_EMPTY, IS_IN_DB, IS_IN_SET

from ..common import Field, db

# # Define your tables here:
# 
# db.define_table('thing',
#     Field('name', 'string', required=True, requires=IS_NOT_EMPTY()),
#     Field('description', 'text', required=True, requires=IS_NOT_EMPTY()),
#     Field('picture', 'upload'),
#     Field('user', 'reference auth_user', required=True, requires=IS_IN_DB(db, 'auth_user.id', '%(first_name)s %(last_name)s')),
#     format='%(name)s',
# )
# 
# # Call db.commit() at the end:
# 
# db.commit()

