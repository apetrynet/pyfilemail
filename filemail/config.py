# -*- coding: utf-8 -*-
import os
#TODO: Replace with py3 compatible import
from ConfigParser import ConfigParser

from errors import FMConfigError


class Config():

    def __init__(self, user, config_path=None):
        self._username = user
        self._config_file = self._locateConfig(config_path)
        self._config = self._parse(self._username)

    def getURL(self, action):
        base_url = 'https://www.filemail.com'
        api_urls = {
            'login': 'api/authentication/login',
            'logout': 'api/authentication/logout',
            'init': 'api/transfer/initialize',
            'get': 'api/transfer/get',
            'complete': 'api/transfer/complete',
            'forward': 'api/transfer/forward',
            'share': 'api/transfer/share',
            'cancel': 'api/transfer/cancel',
            'delete': 'api/transfer/delete',
            'zip': 'api/transfer/zip',
            'file_rename': 'api/transfer/file/rename',
            'file_delete': 'api/transfer/file/delete',
            'update': 'api/transfer/update',
            'sent_get': 'api/transfer/sent/get',
            'received_get': 'api/transfer/received/get',
            'user_get': 'api/user/get',
            'user_update': 'api/user/update'
            }

        if action in api_urls:
            login_url = os.path.join(base_url, api_urls[action])
            return login_url

        raise FMConfigError('You passed an invalid action: {}'.format(action))

    def save(self, user, config_path=None):
        if config_path:
            if not os.path.isfile(config_path):
                os.path.join(config_path, 'filemail.cfg')
        else:
            config_path = self._config_file

        config = ConfigParser()
        config.add_section(self._username)
        for key, value in self._config.items():
            config.set(self._username, key, value)

        config.write(open(config_path, 'w'))

    def _parse(self, user):
        config = self._read()
        if user in config.sections():
            env = dict(config.items(user))

            if not env.get('username'):
                message = 'No username found in {}'.format(self._config_file)
                raise FMConfigError(message)
            if not env.get('api_key'):
                message = 'No api_key found in {}'.format(self._config_file)

            return env

        return {'username': user, 'api_key': None, 'password': None}

    def _read(self):
        config = ConfigParser()
        config.readfp(open(self._config_file))
        return config

    def _locateConfig(self, config_path):

        locations = [
            os.getenv('FILEMAIL_CONFIG_PATH', ''),
            os.path.join(os.path.expanduser('~'), 'filemail.cfg'),
            os.path.join(os.path.dirname(__file__), 'filemail.cfg')
            ]

        if config_path:
            if os.path.isfile(config_path):
                return config_path

        for path in locations:
            if os.path.isfile(path):
                if os.path.basename(path) == 'filemail.cfg':
                    return path

        raise FMConfigError('No filemail.cfg file found.')

    def __getattr__(self, attr):
        if attr in self._config:
            return self._config[attr]

        raise AttributeError(attr)

    def __getitem__(self, key):
        return self._config[key]

    def __setitem__(self, key, value):
        self._config[key] = value

    def __repr__(self):
        return self.config