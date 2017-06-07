# aaa --foo --bar
# bbb <path>
# ccc --foo=<path> --bar <value> <path>
# ddd <color>
# eee --user=<user>


import os
import sqlite3


def complete_color(arg, prefix):
    return ['red', 'yellow', 'green', 'blue']


def complete_user(arg, prefix):
    path  = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'users.db')
    query = 'SELECT username FROM users WHERE username LIKE ?'
    with sqlite3.connect(path) as con:
        return [row[0] for row in con.execute(query, (prefix+'%',))]
