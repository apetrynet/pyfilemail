# -*- coding: utf-8 -*-
import os
import requests
from hashlib import md5
from uuid import uuid4
from mimetypes import guess_type
from datetime import datetime, timedelta
from calendar import timegm

from config import Config
from errors import *


class User():

    def __init__(self, user, api_key, password, **kwargs):
        self._logged_in = False

        self._config = Config(user)
        self.username = self._config.username
        self._config['api_key'] = self._config.apikey or api_key
        self._config['password'] = self._config.password or password

        self._login()

    def getInfo(self):
        url = self._config.getURL('user_get')

        payload = {
            'apikey': self._config.apikey,
            'logintoken': self._config.logintoken
            }

        res = requests.post(url=url, params=payload)

        if not res.ok:
            print res.json()['errormessage']
        return res.json()

    def updateInfo(self, **kwargs):
        self._config.update(kwargs)

        url = self._config.getURL('user_update')

        res = requests.post(url=url, params=self._config)

        if not res.ok:
            print res.json()['errormessage']
        return res.json()

    def getSent(self, get_all=True):
        url = self._config.getURL('sent_get')

        payload = {
            'apikey': self._config.apikey,
            'logintoken': self._config.logintoken,
            'getall': get_all
            }

        res = requests.post(url=url, params=payload)

        if not res.ok:
            print res.json()['errormessage']
        return res.json()

    def getReceived(self, age=None, for_all=True):
        url = self._config.getURL('received_get')

        if age:
            if not isinstance(age, int) or age < 0 or age > 90:
                raise FMBaseError('Age must be integer between 0-90')

            past = datetime.utcnow() - timedelta(days=age)
            age = timegm(past.utctimetuple())

        payload = {
            'apikey': self._config.apikey,
            'logintoken': self._config.logintoken,
            'getForAllUsers': for_all,
            'from': age
            }

        res = requests.post(url=url, params=payload)

        if not res.ok:
            print res.json()['errormessage']
        return res.json()

    def getConfig(self):
        return self._config

    def save(self, config_path=None):
        self._config.save(config_path)

    def _login(self):
        self._connection('login')

    def logout(self):
        self._connection('logout')
        return

    def _connection(self, action):
        if action not in ['login', 'logout']:
            raise FMBaseError('{}, is not a vaid action'.format(action))

        url = self._config.getURL(action)
        auth_keys = {
            'login': ['apikey', 'username', 'password', 'source', 'logintoken'],
            'logout': ['apikey', 'logintoken']
            }

        payload = map(lambda k: (k, self._config[k]), auth_keys[action])

        res = requests.post(
            url=url,
            params=dict(payload)
            )

        if not res.ok:
            print res.json()['errormessage']

        if action == 'login':
            login_token = res.json()['logintoken']
            self._config['logintoken'] = login_token

        self._logged_in = not self._logged_in


class Transfer():

    def __init__(self, user, **kwargs):
        self._user = user
        self._config = self._user.getConfig()
        self._transfer_info = kwargs
        self._transfer_info.update({'from': self._user.username})

        response = self._initialize()

        self.transferid = response['transferid']
        self.transferkey = response['transferkey']
        self.transferurl = response['transferurl']

        print response

    def addfile(self, file_path, **kwargs):
        if not os.path.isfile:
            raise FMBaseError('No such file: {}'.format(file_path))

        url = self.transferurl

        file_specs = self._getFileSpecs(file_path)

        payload = {
            'transferid': self.transferid,
            'transferkey': self.transferkey,
            'fileid': file_specs['fileid'],
            'thefilename': file_specs['filename'],
            'chunkpos': 0,
            'totalsize': file_specs['filesize'],
            'md5': file_specs['md5'],
            'compressed': file_specs['compressed'],
            'name': file_specs['filename'],
            'filename': file_specs['filename'],
            'content-type': file_specs['content-type']
            }

        res = requests.post(url=url,
                            files={'file': open(file_path, 'rb')},
                            data=payload,
                            hooks=dict(response=self.print_url),
                            stream=True)
        print res

    def print_url(self, r, *args, **kwargs):
        print r.iter_lines()

    def complete(self, keep_transfer_key=False):
        url = self._config.getURL('complete')

        payload = {
            'apikey': self._config.apikey,
            'transferid': self.transferid,
            'transferkey': self.transferkey,
            'keep_transfer_key': keep_transfer_key
            }

        res = requests.post(url=url, params=payload)

        if not res.ok:
            print res.json()['errormessage']
        print res.json()

    def delete(self):
        url = self._config.getURL('delete')

        payload = {
            'apikey': self._config.apikey,
            'transferid': self.transferid,
            'logintoken': self._config.logintoken
            }

        res = requests.post(url=url, params=payload)

        if not res.ok:
            print res.json()['errormessage']
        print res.json()

    def zip(self):
        url = self._config.getURL('zip')

        payload = {
            'apikey': self._config.apikey,
            'transferid': self.transferid,
            'transferkey': self.transferkey
            }

        res = requests.post(url=url, params=payload)

        if not res.ok:
            print res.json()['errormessage']
        print res.json()

    def cancel(self):
        url = self._config.getURL('cancel')

        payload = {
            'apikey': self._config.apikey,
            'transferid': self.transferid,
            'transferkey': self.transferkey
            }

        res = requests.post(url=url, params=payload)

        if not res.ok:
            print res.json()['errormessage']
        print res.json()

    def share(self, to=[], message=u''):
        url = self._config.getURL('share')

        payload = {
            'apikey': self._config.apikey,
            'logintoken': self._config.logintoken,
            'transferid': self.transferid,
            'to': ','.join(to),
            'from': self._config.username,
            'message': message
            }

        res = requests.post(url=url, params=payload)

        if not res.ok:
            print res.json()['errormessage']
        print res.json()

    def forward(self, to=[]):
        url = self._config.getURL('forward')

        payload = {
            'apikey': self._config.apikey,
            'transferid': self.transferid,
            'transferkey': self.transferkey,
            'to': ','.join(to)
            }

        res = requests.post(url=url, params=payload)

        if not res.ok:
            print res.json()['errormessage']
        print res.json()

    def get(self):
        url = self._config.getURL('get')

        payload = {
            'apikey': self._config.apikey,
            'transferid': self.transferid,
            'logintoken': self._config.logintoken
            }

        res = requests.post(url=url, params=payload)

        if not res.ok:
            print res.json()['errormessage']
        print res.json()

    def update(self, **kwargs):
        url = self._config.getURL('update')

        payload = {
            'apikey': self._config.apikey,
            'logintoken': self._config.logintoken,
            'transferid': self.transferid,
            'message': kwargs.get('message'),
            'days': kwargs['days'],
            'downloads': kwargs['downloads'],
            'notify': kwargs['notify']
            }

        res = requests.post(url=url, params=payload)

        if not res.ok:
            print res.json()['errormessage']
        print res.json()

    def _getFileSpecs(self, file_path):
        fileid = uuid4()
        md5hash = md5(open(file_path, 'rb').read()).digest()
        compressed = file_path[-3:] in ['zip', 'rar', 'tar', '.gz']

        results = {
            'fileid': str(fileid).replace('-', ''),
            'filename': os.path.basename(file_path),
            'filesize': os.path.getsize(file_path),
            'md5': md5hash.encode('base64')[:-1],
            'compressed': compressed,
            'content-type': guess_type(file_path)[0]
            }

        return results

    def _initialize(self):
        payload = {
            'apikey': self._config.apikey,
            'logintoken': self._config.logintoken,
            }
        payload.update(self._transfer_info)

        url = self._config.getURL('init')

        res = requests.post(url=url, params=payload)
        if not res:
            raise FMBaseError(res.status_code)

        return res.json()


class Contacts():

    def __init__(self):
        super(Contacts, self).__init__()


class Company():

    def __init__(self):
        super(Company, self).__init__()