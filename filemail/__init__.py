# -*- coding: utf-8 -*-
from users import User
from transfer import Transfer
from config import Config
from fmfile import FMFile
from http import FMConnection


__title__ = 'filemail'
__version__ = '0.0.9'
__author__ = 'Daniel Flehner Heen'
__license__ = 'MIT'
__copyright__ = 'Copyright 2014 Daniel Flehner Heen'


def login(username, apikey=None, password=None, **kwargs):
    """Convenience function to login to filemail.

    :param username: String with filemail username (usually email address)
    :param apikey: String (optional) with key provided by filemail support
    :param password: String (optional) with valid password
    :param \*\*kwargs: Additional `key=value` pairs with user setings
    :returns: :class:`User <User>` object

    `apikey` and `password` are only optional if you've stored login information
    in a :ref:`configfile <example-configfile>`
    """

    user = User(username, apikey, password, **kwargs)
    user.login()
    return user
