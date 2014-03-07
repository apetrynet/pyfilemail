# -*- coding: utf-8 -*-
import os
#TODO: Replace with py3 compatible import
from ConfigParser import ConfigParser

from errors import FMConfigError


class Config():

    def __init__(self):
        self._config = self._parse()

    def _parse(self):
        config = self._read()
        environment = {}
        for section in config.sections():
            env = dict(config.items(section))
            environment[section] = env
        return environment

    def _read(self):
        config = ConfigParser()
        config_file = self._locateConfig()
        config.readfp(open(config_file))
        return config

    def _locateConfig(self):

        locations = [
            os.getenv('FILEMAIL_CONFIG_PATH', ''),
            os.path.join(os.path.expanduser('~'), 'filemail.cfg'),
            os.path.join(os.path.dirname(__file__), 'filemail.cfg')
            ]

        for path in locations:
            if os.path.isfile(path):
                if os.path.basename(path) == 'filemail.cfg':
                    return path
        raise FMConfigError('No filemail.cfg file found.')

    def __getitem__(self, item):
        if item in self._config:
            return self._config[item]

        raise KeyError(item)

    def __repr__(self):
        return self.config