# -*- coding: utf-8 -*-
import os
from ConfigParser import ConfigParser

from errors import FMConfigError


class Config():
    """Config handles creating, loading or storing :class: `User` settings."""

    def __init__(self, username, **kwargs):
        self._config = {}

        self.required_keys = [
            'apikey',
            'password',
            'username'
            ]

        self.optional_keys = [
            'country',
            'created',
            'defaultconfirmation',
            'defaultdays',
            'defaultdownloads',
            'defaultnotify',
            'defaultsubject',
            'email',
            'logintoken',
            'maxdays',
            'maxdownloads',
            'maxtransfersize',
            'membershipname',
            'name',
            'newsletter',
            'signature',
            'source',
            'subscription'
            ]

        self.valid_keys = self.required_keys + self.optional_keys
        self.set('username', username)

        if kwargs:
            self.update(kwargs)

    def set(self, key, value):
        if self.validKey(key):
            if key in self.required_keys:
                if value is None:
                    msg = 'Required key, "%s", can\'t be None' % key
                    raise FMConfigError(msg)
            self._config[key] = value
        else:
            raise AttributeError('Non valid config key, "%s" passed' % key)

    def get(self, key):
        if key in self._config:
            return self._config[key]
        return None

    def update(self, config=None):
        if config is None:
            return
        if not isinstance(config, dict):
            raise Exception('You need to pass a dict')

        for key, value in config.items():
            self.set(key, value)

    def dump(self):
        return self._config

    def validKey(self, key):
        return key in self.valid_keys

    def save(self, config_file=None):

        config = ConfigParser()
        config.add_section(self._username)
        for key, value in self._config.items():
            config.set(self._username, key, value)

        config.write(open(config_file, 'w'))

    def load(self, config_file):
        if config_file is None:
            config_file = self._locateConfig()

        if config_file is None:
            raise FMConfigError('No config file found')

        config = self._read(config_file)
        username = self.get('username')

        if username in config.sections():
            env = dict(config.items(username))

            for key, value in env.items():
                self.set(key, value)

    def _read(self, config_file):
        config = ConfigParser()
        config.readfp(open(config_file))
        return config

    def _locateConfig(self):
        here = os.path.dirname(__file__)
        locations = [
            os.getenv('FILEMAIL_CONFIG_PATH', ''),
            os.path.join(os.path.dirname(here), 'filemail.cfg'),
            os.path.join(os.path.expanduser('~'), 'filemail.cfg')
            ]

        for path in locations:
            if os.path.isfile(path):
                if os.path.basename(path) == 'filemail.cfg':
                    return path

        return None

    def __repr__(self):
        return repr(self._config)