# -*- coding: utf-8 -*-
from users import User
from transfer import Transfer
from config import Config
from fmfile import FMFile


__title__ = 'filemail'
__version__ = '0.1.0'
__author__ = 'Daniel Flehner Heen'
__license__ = 'MIT'
__copyright__ = 'Copyright 2014 Daniel Flehner Heen'


def login(username, apikey=None, password=None, **kwargs):
    user = User(username, apikey, password, **kwargs)
    user.login()
    return user
