# -*- coding: utf-8 -*-

__title__ = 'pyfilemail'
__version__ = '0.2.3'
__author__ = 'Daniel Flehner Heen'
__license__ = 'MIT'
__copyright__ = 'Copyright 2016 Daniel Flehner Heen'


import os
import logging
from functools import wraps

import appdirs

# Init logger
logger = logging.getLogger('pyfilemail')

level = os.getenv('PYFILEMAÌL_DEBUG') and logging.DEBUG or logging.INFO
logger.setLevel(level)

# Formatter
format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
formatter = logging.Formatter(format_string)

# File logger setup
datadir = appdirs.user_data_dir(appname='pyfilemail', version=__version__)
if not os.path.exists(datadir):
    os.makedirs(datadir)

logfile = os.path.join(datadir, 'pyfilemail.log')

filehandler = logging.FileHandler(logfile)
filehandler.setLevel(level)
filehandler.setFormatter(formatter)

# Stream logger
streamhandler = logging.StreamHandler()
streamhandler.setLevel(logging.WARNING)

# Add handler
logger.addHandler(filehandler)
logger.addHandler(streamhandler)


# Decorator to make sure user is logged in
from errors import FMBaseError


def login_required(f):
    """Decorator function to check if user is loged in.

    :raises: :class:`FMBaseError` if not logged in
    """

    @wraps(f)
    def check_login(cls, *args, **kwargs):
        if not cls.logged_in:
            raise FMBaseError('Please login to use this method')

        return f(cls, *args, **kwargs)

    return check_login


from users import User  # lint:ok
from transfer import Transfer  # lint:ok