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
        self.username = username

        self.config = Config(self.username)
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
        self.validateLoginStatus()

        url = getURL('user_get')

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.config.get('logintoken')
            }

        res = requests.post(url=url, params=payload)

        if not res.ok:
            print res.json()['errormessage']
        return res.json()

    def updateUserInfo(self, info):
        self.validateLoginStatus()

        self.config.update(info)

        url = getURL('user_update')

        res = requests.post(url=url, params=self.config.dump())

        if not res.ok:
            print res.json()['errormessage']
        return res.json()

    def getSent(self, expired=False):
        self.validateLoginStatus()

        url = getURL('sent_get')

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.config.get('logintoken'),
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
        self.validateLoginStatus()

        url = getURL('received_get')

        if age:
            if not isinstance(age, int) or age < 0 or age > 90:
                raise FMBaseError('Age must be integer between 0-90')

            past = datetime.utcnow() - timedelta(days=age)
            age = timegm(past.utctimetuple())

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.config.get('logintoken'),
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

    def validateLoginStatus(self):
        if self._logged_in:
            return True
        raise Exception('You must be logged in')

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
        self._files = []
        self.config = self._user.config
        self._transfer_info = dict(kwargs)
        self._transfer_info.update({'from': self._user.username})

        if 'status' not in self._transfer_info:
            self._transfer_info.update(self._initialize())

        if 'id' in self._transfer_info:
            self.transferid = self._transfer_info.get('id')
        else:
            self.transferid = self._transfer_info.get('transferid')

    def addFile(self, filename):
        if not os.path.isfile(filename):
            raise FMBaseError('No such file: {}'.format(filename))

        fmfile = FMFile(filename)
        self._files.append(fmfile)

    def addFiles(self, files):
        for filename in files:
            self.addFile(filename)

    def files(self):
        return self._files

    def send(self, callback=None):
        url = self._transfer_info.get('transferurl')

        for fmfile in self._files:
            fmfile.set('transferid', self._transfer_info['transferid'])
            fmfile.set('transferkey', self._transfer_info['transferkey'])
            print fmfile.payload()
            res = requests.post(url=url,
                                params=fmfile.payload(),
                                data=self.fileStreamer(fmfile, callback),
                                stream=True)

            if not res.ok:
                print res
                return False
        self.complete()

    def fileStreamer(self, fmfile, callback=None):
        chunksize = 65536
        incr = 100.0 / (fmfile.get('totalsize') / chunksize)
        count = 0
        data = None
        with open(fmfile.fullpath, 'rb') as f:
            while True:
                data = f.read(chunksize)
                fmfile.set('chunkpos', f.tell())
                if not data:
                    break

                if callback is not None:
                    callback(int(incr * count))

                count += 1

                yield data

    def complete(self, keep_transfer_key=False):
        url = getURL('complete')

        payload = {
            'apikey': self.config.get('apikey'),
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
            'apikey': self.config.get('apikey'),
            'transferid': self._transfer_info.get('transferid'),
            'logintoken': self.config.get('logintoken')
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
            'apikey': self.config.get('apikey'),
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
            'apikey': self.config.get('apikey'),
            'logintoken': self.config.get('logintoken'),
            'transferid': self._transfer_info.get('transferid'),
            'to': ','.join(list(to)),
            'from': self.config.get('username'),
            'message': message
            }

        res = requests.post(url=url, params=payload)

        if not res.ok:
            print res.json()['errormessage']
        print res.json()

    def forward(self, to=[]):
        url = getURL('forward')

        payload = {
            'apikey': self.config.get('apikey'),
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
            'apikey': self.config.get('apikey'),
            'transferid': self.transferid,
            'logintoken': self.config.get('logintoken')
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
            'apikey': self.config.get('apikey'),
            'logintoken': self.config.get('logintoken'),
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
            'apikey': self.config.get('apikey'),
            'logintoken': self.config.get('logintoken'),
            }
        payload.update(self._transfer_info)

        url = getURL('init')

        res = requests.post(url=url, params=payload)
        if not res.ok:
            print res.status_code
            raise FMBaseError(res.status_code)
        return res.json()

    def __repr__(self):
        return repr(self._transfer_info)


class FMFile():

    def __init__(self, fullpath=None, data=None):
        self._payload = {}
        self.fullpath = fullpath
        self.path = None
        self.filename = None

        if self.fullpath is not None:
            self.addFile(self.fullpath)

        if data is not None:
            self.updatePayload(data)

    def addFile(self, filename):
        if not os.path.isfile(filename):
            raise Exception('No such file: {}'.format(filename))

        self.path, self.filename = os.path.split(filename)

        self.updatePayload(self.getFileSpecs())

    def download(self, path):
        pass

    def set(self, key, value):
        self._payload[key] = value

    def get(self, key):
        if key in self._payload:
            return self._payload[key]

        return None

    def updatePayload(self, data):
        if not isinstance(data, dict):
            raise Exception('A dict must be passed')

        for key, value in data.items():
            self.set(key, value)

    def payload(self):
        return self._payload

    def getFileSpecs(self):
        fileid = str(uuid4()).replace('-', '')
        md5hash = md5(open(self.fullpath, 'rb').read()).digest()
        compressed = self.filename[-3:] in ['zip', 'rar', 'tar', '.gz', '.7z']

        specs = {
            'fileid': fileid,
            'filename': self.filename,
            'thefilename': self.filename,
            'totalsize': os.path.getsize(self.fullpath),
            'md5': md5hash.encode('base64')[:-1],
            'compressed': compressed,
            'content-type': guess_type(self.fullpath)[0],
            'chunkpos': 0
            }

        return specs

    def __repr__(self):
        return repr(self.payload())


class Contacts():

    def __init__(self):
        super(Contacts, self).__init__()


class Company():

    def __init__(self):
        super(Company, self).__init__()