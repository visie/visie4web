import re
import getpass
from apps._default.common import auth, db, groups

def createuser():
    email = ''
    while not re.match(r"[^@ ]+@[^@ ]+\.[^@ ]+", email):
        email = input('Email: ')
    first_name = input('First Name: ')
    last_name = input('Last Name: ')

    password = 'a'
    password2 = 'b'

    while password != password2:
        password = getpass.getpass('Password: ')
        password2 = getpass.getpass('Password (again): ')
        if password != password2:
            print('Passwords do not match')

    uer_groups = [i for i in input('Groups (space separated): ').split() if i]

    user = auth.register({'first_name':first_name, 'last_name':last_name, 'email': email, 'password':password})

    if user['errors']:
        print('Errors: \n -', '\n -'.join(user['errors']))
        return 1

    db(db.auth_user.id==user['id']).update(action_token='')

    for group in uer_groups:
        groups.add(user['id'], group)

    db.commit()
    return 0
