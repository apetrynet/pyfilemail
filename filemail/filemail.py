# -*- coding: utf-8 -*-
import os
import requests
from hashlib import md5
from uuid import uuid4
from mimetypes import guess_type
from datetime import datetime, timedelta
from calendar import timegm

from urls import getURL
from config import Config
from errors import *


class User():

    def __init__(self, username, apikey=None, password=None, **kwargs):
        self._logged_in = False

        self.config = Config(username)
        if apikey and password:
            self.config.set('apikey', apikey)
            self.config.set('password', password)
            for key, value in kwargs.items():
                self.config.set(key, value)

        else:
            if 'config_file' in kwargs:
                config_file = kwargs['config_file']

            else:
                config_file = None

            self.config.load(config_file)

    def getInfo(self):
        url = getURL('user_get')

        payload = {
            'apikey': self.config.apikey,
            'logintoken': self.config.logintoken
            }

        res = requests.post(url=url, params=payload)

        if not res.ok:
            print res.json()['errormessage']
        return res.json()

    def updateInfo(self, **kwargs):
        self.config.update(kwargs)

        url = getURL('user_update')

        res = requests.post(url=url, params=self.config)

        if not res.ok:
            print res.json()['errormessage']
        return res.json()

    def getSent(self, expired=False):
        url = getURL('sent_get')

        payload = {
            'apikey': self.config.apikey,
            'logintoken': self.config.logintoken,
            'getall': expired
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
        url = getURL('received_get')

        if age:
            if not isinstance(age, int) or age < 0 or age > 90:
                raise FMBaseError('Age must be integer between 0-90')

            past = datetime.utcnow() - timedelta(days=age)
            age = timegm(past.utctimetuple())

        payload = {
            'apikey': self.config.apikey,
            'logintoken': self.config.logintoken,
            'getForAllUsers': for_all,
            'from': age
            }

        res = requests.post(url=url, params=payload)

        if not res.ok:
            print res.json()['errormessage']
        return res.json()

    def getConfig(self):
        return self.config

    def save(self, config_path=None):
        self.config.save(config_path)

    def login(self):
        self._connection('login')

    def logout(self):
        self._connection('logout')
        return

    def _connection(self, action):
        if action not in ['login', 'logout']:
            raise FMBaseError('{}, is not a vaid action'.format(action))

        url = getURL(action)
        auth_keys = {
            'login': ['apikey', 'username', 'password', 'source', 'logintoken'],
            'logout': ['apikey', 'logintoken']
            }

        payload = map(lambda k: (k, self.config.get(k)), auth_keys[action])

        res = requests.post(
            url=url,
            params=dict(payload)
            )

        if not res.ok:
            print res.json()['errormessage']

        if action == 'login':
            login_token = res.json()['logintoken']
            self.config.set('logintoken', login_token)

        self._logged_in = not self._logged_in


class Transfer():

    def __init__(self, user, **kwargs):
        self._user = user
        self.config = self._user.getConfig()
        self._transfer_info = dict(kwargs)
        self._transfer_info.update({'from': self._user.username})

        self.files = list()

        if 'status' not in self._transfer_info:
            self._transfer_info.update(self._initialize())

        if 'id' in self._transfer_info:
            self.transferid = self._transfer_info.get('id')
        else:
            self.transferid = self._transfer_info.get('transferid')

    def addfile(self, file_path, callback=None, chunksize=2048):
        if not os.path.isfile:
            raise FMBaseError('No such file: {}'.format(file_path))

        url = self._transfer_info.get('transferurl')

        fm_file = FMFile(self, file_path)

        def feedMe(url):
            incr = 100.0 / (fm_file.payload['totalsize'] / chunksize)
            count = 0
            with open(url, 'rb') as f:
                while True:
                    count += 1
                    data = f.read(chunksize)
                    if not data:
                        break

                    if callback is not None:
                        callback(int(incr * count))

                    yield data

        res = requests.post(url=url,
                            params=fm_file.payload,
                            data=feedMe(file_path))

        if not res.ok:
            print res.json()['errormessage']
            return False
        return True

    def complete(self, keep_transfer_key=False):
        url = getURL('complete')

        payload = {
            'apikey': self.config.apikey,
            'transferid': self._transfer_info.get('transferid'),
            'transferkey': self._transfer_info.get('transferkey'),
            'keep_transfer_key': keep_transfer_key
            }

        res = requests.post(url=url, params=payload)

        if not res.ok:
            print res.json()['errormessage']
        print res.json()

    def delete(self):
        url = getURL('delete')

        payload = {
            'apikey': self.config.apikey,
            'transferid': self._transfer_info.get('transferid'),
            'logintoken': self.config.logintoken
            }

        res = requests.post(url=url, params=payload)

        if not res.ok:
            print res.json()['errormessage']
        print res.json()

    def zip(self):
        url = getURL('zip')

        payload = {
            'apikey': self.config.apikey,
            'transferid': self._transfer_info.get('transferid'),
            'transferkey': self._transfer_info.get('transferkey')
            }

        res = requests.post(url=url, params=payload)

        if not res.ok:
            print res.json()['errormessage']
        print res.json()

    def cancel(self):
        url = getURL('cancel')

        payload = {
            'apikey': self.config.apikey,
            'transferid': self._transfer_info.get('transferid'),
            'transferkey': self._transfer_info.get('transferkey')
            }

        res = requests.post(url=url, params=payload)

        if not res.ok:
            print res.json()['errormessage']
        print res.json()

    def share(self, to=[], message=u''):
        url = getURL('share')

        payload = {
            'apikey': self.config.apikey,
            'logintoken': self.config.logintoken,
            'transferid': self._transfer_info.get('transferid'),
            'to': ','.join(list(to)),
            'from': self.config.username,
            'message': message
            }

        res = requests.post(url=url, params=payload)

        if not res.ok:
            print res.json()['errormessage']
        print res.json()

    def forward(self, to=[]):
        url = getURL('forward')

        payload = {
            'apikey': self.config.apikey,
            'transferid': self._transfer_info.get('transferid'),
            'transferkey': self._transfer_info.get('transferkey'),
            'to': ','.join(to)
            }

        res = requests.post(url=url, params=payload)

        if not res.ok:
            print res.json()['errormessage']
        print res.json()

    def getFiles(self):
        url = getURL('get')

        payload = {
            'apikey': self.config.apikey,
            'transferid': self.transferid,
            'logintoken': self.config.logintoken
            }

        res = requests.post(url=url, params=payload)

        if not res.ok:
            print res.json()['errormessage']

        self._transfer_info.update(res.json()['transfer'])
        files = self._transfer_info['files']

        del(self._transfer_info['files'])

        for file_data in files:
            self.files.append(FMFile(transfer=self,
                                     file_data=file_data))

        return self.files

    def update(self, **kwargs):
        url = getURL('update')

        payload = {
            'apikey': self.config.apikey,
            'logintoken': self.config.logintoken,
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
            'apikey': self.config.apikey,
            'logintoken': self.config.logintoken,
            }
        payload.update(self._transfer_info)

        url = getURL('init')

        res = requests.post(url=url, params=payload)
        if not res.ok:
            print res.status_code
            raise FMBaseError(res.status_code)
        return res.json()


class FMFile(object):

    def __init__(self, transfer=None, file_path=None, file_data=None):
        #if not isinstance(transfer, (Transfer, dict)):
            #raise FMBaseError('Please pass a Transfer or dict object as arg0')

        self.payload = {
            'transferid': None,
            'transferkey': None,
            'fileid': None,
            'thefilename': None,
            'chunkpos': 0,
            'totalsize': None,
            'md5': None,
            'compressed': None,
            'filename': None,
            'content-type': None
            }

        if transfer:
            self.payload.update(transfer._transfer_info)

        if file_path:
            self.file_path = self._addFile(file_path)
            self._updatePayload(file_path)

        if file_data:
            self._updatePayload(file_data=file_data)
        #print self.payload

    def download(self):
        pass

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
        return repr(self.payload)


class Contacts():

    def __init__(self):
        super(Contacts, self).__init__()


class Company():

    def __init__(self):
        super(Company, self).__init__()