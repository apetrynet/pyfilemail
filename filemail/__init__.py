# -*- coding: utf-8 -*-
from filemail import User, Transfer, Config


def login(username, apikey=None, password=None, **kwargs):
    user = User(username, apikey, password, **kwargs)
    user.login()
    return user
