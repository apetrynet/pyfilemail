# -*- coding: utf-8 -*-
from filemail import User, Transfer  # lint:ok


def login(user, api_key=None, password=None, **kwargs):
    user = User(user, api_key, password, **kwargs)
    return user
