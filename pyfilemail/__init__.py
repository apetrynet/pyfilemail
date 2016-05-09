# -*- coding: utf-8 -*-

__title__ = 'pyfilemail'
__version__ = '0.1.0'
__author__ = 'Daniel Flehner Heen'
__license__ = 'MIT'
__copyright__ = 'Copyright 2016 Daniel Flehner Heen'


import os
import logging

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