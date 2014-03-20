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

        #return res.json()
        transfers = list()
        for transfer in res.json()['transfers']:
            transfers.append(Transfer(self, **transfer))
        return transfers

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
        self._transfer_info = dict(kwargs)
        self._transfer_info.update({'from': self._user.username})

        self.files = list()

        if 'status' not in self._transfer_info:
            print 'init'
            self._transfer_info.update(self._initialize())

        print self._transfer_info

    def addfile(self, file_path):
        if not os.path.isfile:
            raise FMBaseError('No such file: {}'.format(file_path))

        url = self._transfer_info.get('transferurl')

        fm_file = FMFile(self, file_path)

        res = requests.post(url=url,
                            files={'file': open(file_path, 'rb')},
                            data=fm_file.payload)

        if not res.ok:
            print res.json()['errormessage']
            return False
        return True

    def complete(self, keep_transfer_key=False):
        url = self._config.getURL('complete')

        payload = {
            'apikey': self._config.apikey,
            'transferid': self._transfer_info.get('transferid'),
            'transferkey': self._transfer_info.get('transferkey'),
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
            'transferid': self._transfer_info.get('transferid'),
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
            'transferid': self._transfer_info.get('transferid'),
            'transferkey': self._transfer_info.get('transferkey')
            }

        res = requests.post(url=url, params=payload)

        if not res.ok:
            print res.json()['errormessage']
        print res.json()

    def cancel(self):
        url = self._config.getURL('cancel')

        payload = {
            'apikey': self._config.apikey,
            'transferid': self._transfer_info.get('transferid'),
            'transferkey': self._transfer_info.get('transferkey')
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
            'transferid': self._transfer_info.get('transferid'),
            'to': ','.join(list(to)),
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
            'transferid': self._transfer_info.get('transferid'),
            'transferkey': self._transfer_info.get('transferkey'),
            'to': ','.join(to)
            }

        res = requests.post(url=url, params=payload)

        if not res.ok:
            print res.json()['errormessage']
        print res.json()

    def getFiles(self):
        url = self._config.getURL('get')

        payload = {
            'apikey': self._config.apikey,
            'transferid': self._transfer_info.get('transferid'),
            'logintoken': self._config.logintoken
            }

        res = requests.post(url=url, params=payload)

        if not res.ok:
            print res.json()['errormessage']

        for file_data in res.json()['transfer']['files']:
            self.files.append(FMFile(file_data))

        return self.files

    def update(self, **kwargs):
        url = self._config.getURL('update')

        payload = {
            'apikey': self._config.apikey,
            'logintoken': self._config.logintoken,
            'transferid': self._transfer_info.get('transferid'),
            'message': kwargs.get('message'),
            'days': kwargs['days'],
            'downloads': kwargs['downloads'],
            'notify': kwargs['notify']
            }

        res = requests.post(url=url, params=payload)

        if not res.ok:
            print res.json()['errormessage']
        print res.json()

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


class FMFile(object):

    def __init__(self, transfer, file_path=None, file_data=None):
        if not isinstance(transfer, (Transfer, dict)):
            raise FMBaseError('Please pass a Transfer or dict object as arg0')

        if isinstance(transfer, dict):
            transfer_id = transfer['id']
            transfer_key = transfer.get('key', None)
        else:
            transfer_id = transfer.transferid
            transfer_key = transfer.transferkey

        self.payload = {
            'transferid': transfer_id,
            'transferkey': transfer_key,
            'fileid': None,
            'thefilename': None,
            'chunkpos': 0,
            'totalsize': None,
            'md5': None,
            'compressed': None,
            'filename': None,
            'content-type': None
            }

        if file_path:
            self.file_path = self._addFile(file_path)
            self._updatePayload(file_path)

        if file_data:
            if not isinstance(file_data, dict):
                raise FMBaseError('file_data must be a dict')

            self._updatePayload(file_data)
        print self.payload

    def _updatePayload(self, file_path=None, file_data=None):
        if file_data:
            if not isinstance(file_data, dict):
                raise FMBaseError('file_data must be a dict')
            self.payload.update(file_data)
            return True
        if file_path:
            self.payload.update(self._getFileSpecs(file_path))
            return True
        return False

    def _addFile(self, file_path):
        if not os.path.isfile(file_path):
            return None

        return file_path

    def _getFileSpecs(self, file_path):
        fileid = str(uuid4()).replace('-', '')
        md5hash = md5(open(file_path, 'rb').read()).digest()
        compressed = file_path[-3:] in ['zip', 'rar', 'tar', '.gz', '.7z']

        specs = {
            'fileid': fileid,
            'filename': os.path.basename(file_path),
            'thefilename': os.path.basename(file_path),
            'totalsize': os.path.getsize(file_path),
            'md5': md5hash.encode('base64')[:-1],
            'compressed': compressed,
            'content-type': guess_type(file_path)[0]
            }

        return specs

    def __setattribute__(self, attr, value):
        if attr == 'file_path':
            self.file_path = self._addFile(value)
            self._updatePayload(value)

        super(FMFile, self).__setattribute__(attr, value)

    def __repr__(self):
        return dict(self.payload)


class Contacts():

    def __init__(self):
        super(Contacts, self).__init__()


class Company():

    def __init__(self):
        super(Company, self).__init__()