# -*- coding: utf-8 -*-

__title__ = 'pyfilemail'
__version__ = '0.5.0'
__author__ = 'Daniel Flehner Heen'
__license__ = 'MIT'
__copyright__ = 'Copyright 2016 Daniel Flehner Heen'


import os
import logging
import json
from functools import wraps
from netrc import netrc, NetrcParseError

# Check for .netrc file
try:
    _netrc = netrc()
    NETRC = True

except (IOError, NetrcParseError):
    NETRC = False

import appdirs

from errors import FMBaseError

# Init logger
logger = logging.getLogger('pyfilemail')

env_level = os.getenv('PYFILEMAÌL_LOG_LEVEL')
if env_level is not None and hasattr(logging, env_level.upper()):
    level = getattr(logging, env_level.uppper())

else:
    level = logging.INFO

logger.setLevel(level)

# Formatter
format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
formatter = logging.Formatter(format_string)

# File logger setup
datadir = appdirs.user_data_dir(appname='pyfilemail')
if not os.path.exists(datadir):
    os.makedirs(datadir)

logfile = os.path.join(datadir, 'pyfilemail.log')

filehandler = logging.FileHandler(logfile)
filehandler.setLevel(level)
filehandler.setFormatter(formatter)

# Stream logger
streamhandler = logging.StreamHandler()
streamhandler.setLevel(logging.INFO)

# Add handler
logger.addHandler(filehandler)
logger.addHandler(streamhandler)


# Holds whether or not we are running as commandline tool
COMMANDLINE = False


# Decorator to make sure user is logged in
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


def load_config():
    """Load configuration file containing API KEY and other settings.

    :rtype: str
    """

    configfile = get_configfile()

    if not os.path.exists(configfile):
        data = {
            'apikey': 'GET KEY AT: https://www.filemail.com/apidoc/ApiKey.aspx'
            }

        save_config(data)

    with open(configfile, 'rb') as f:
        return json.load(f)


def save_config(config):
    """Save configuration file to users data location.

     - Linux: ~/.local/share/pyfilemail
     - OSX: ~/Library/Application Support/pyfilemail
     - Windows: C:\\\Users\\\{username}\\\AppData\\\Local\\\pyfilemail

     :rtype: str
    """

    configfile = get_configfile()

    if not os.path.exists(configfile):
        configdir = os.path.dirname(configfile)

        if not os.path.exists(configdir):
            os.makedirs(configdir)

    data = config

    with open(configfile, 'wb') as f:
        json.dump(data, f, indent=2)


def get_configfile():
    """Return full path to configuration file.

     - Linux: ~/.local/share/pyfilemail
     - OSX: ~/Library/Application Support/pyfilemail
     - Windows: C:\\\Users\\\{username}\\\AppData\\\Local\\\pyfilemail

     :rtype: str
    """

    ad = appdirs.AppDirs('pyfilemail')
    configdir = ad.user_data_dir
    configfile = os.path.join(configdir, 'pyfilemail.cfg')

    return configfile


from users import User  # lint:ok
from transfer import Transfer  # lint:ok