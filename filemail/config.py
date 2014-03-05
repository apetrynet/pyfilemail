# -*- coding: utf-8 -*-
#TODO: Replace with py3 compatible import
from ConfigParser import ConfigParser


config = ConfigParser()
config.readfp(open('filemail.cfg'))
print config.items('Authentication')