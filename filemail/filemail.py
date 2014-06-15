# -*- coding: utf-8 -*-
import os
#from requests import Session
from hashlib import md5
from uuid import uuid4
from mimetypes import guess_type
from datetime import datetime, timedelta
from calendar import timegm

from urls import getURL
from config import Config
from connection import FMConnection
from errors import hellraiser, FMBaseError, FMFileError


class User():

    def __init__(self, username, apikey=None, password=None, **kwargs):
        self._logged_in = False
        self._transfers = []
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

        self.session = FMConnection(self)

    def getInfo(self):
        self.validateLoginStatus()

        url = getURL('user_get')

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.config.get('logintoken')
            }

        res = self.session.post(url=url, params=payload)

        if not res.ok:
            hellraiser(res.json())

        return res.json()

    def updateUserInfo(self, info):
        self.validateLoginStatus()

        self.config.update(info)

        url = getURL('user_update')

        res = self.session.post(url=url, params=self.config.dump())

        if not res.ok:
            hellraiser(res.json())

        return res.json()

    def getSent(self, expired=False):
        self.validateLoginStatus()

        url = getURL('sent_get')

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.config.get('logintoken'),
            'getall': expired
            }

        res = self.session.post(url=url, params=payload)

        if not res.ok:
            hellraiser(res.json())

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

        res = self.session.post(url=url, params=payload)

        if not res.ok:
            hellraiser(res.json())

        return res.json()

    def getConfig(self):
        return self.config

    def save(self, config_path=None):
        self.config.save(config_path)

    def login(self):
        state = self.session.login()
        self._setLoginState(state)

    def logout(self):
        self.checkAllTransfers()

        state = self.session.logout()
        self._setLoginState(state)

    def validateLoginStatus(self):
        if self._logged_in:
            return True
        raise FMBaseError('You must be logged in')

    def addTransfer(self, transfer):
        if transfer not in self._transfers:
            self._transfers.append(transfer)

    def transfers(self):
        return self._transfers

    def checkAllTransfers(self):
        for transfer in self.transfers():
            if not transfer.isComplete():
                error = {
                    'errorcode': 4003,
                    'errormessage': 'You must complete transfer before logout.'
                    }
                hellraiser(error)

    def _setLoginState(self, state):
        self._logged_in = state


class Transfer():

    def __init__(self, user, **kwargs):
        self._user = user
        self._user.addTransfer(self)
        self._files = []
        self._complete = True
        self.config = self._user.config
        self.session = self._user.session
        self.transfer_info = dict(kwargs)
        self.transfer_info.update({'from': self._user.username})

        if 'status' not in self.transfer_info:
            self.transfer_info.update(self._initialize())

        self.transferid = self.getTransferID()

    def addFile(self, filename):
        if isinstance(filename, FMFile):
            fmfile = filename
        else:
            if not os.path.isfile(filename):
                raise FMBaseError('No such file: {}'.format(filename))

            fmfile = FMFile(filename)

        self._files.append(fmfile)

        self._complete = False

    def addFiles(self, files):
        for filename in files:
            self.addFile(filename)

    def files(self):
        return self._files

    def getTransferID(self):
        if 'transferid' in self.transfer_info:
            transferid = self.transfer_info.get('transferid')
        else:
            transferid = self.transfer_info.get('id')

        return transferid

    def send(self, callback=None, auto_complete=True):
        url = self.transfer_info.get('transferurl')

        for fmfile in self._files:
            fmfile.set('transferid', self.transferid)
            fmfile.set('transferkey', self.transfer_info['transferkey'])

            res = self.session.post(url=url,
                                    params=fmfile.fileInfo(),
                                    data=self.fileStreamer(fmfile,
                                                           callback),
                                    stream=True)

            res.text

            if not res.ok:
                hellraiser(res.json())

        if auto_complete:
            self.complete(keep_transfer_key=True)

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
            'transferid': self.transferid,
            'transferkey': self.transfer_info.get('transferkey'),
            'keep_transfer_key': keep_transfer_key
            }

        res = self.session.post(url=url, params=payload)

        if not res.ok:
            hellraiser(res.json())

        self._complete = True
        print res.json()

    def isComplete(self):
        return self._complete

    def update(self, **kwargs):
        '''Update an completed transfer'''

        url = getURL('update')

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.config.get('logintoken'),
            'transferid': self.transferid,
            'message': kwargs.get('message'),
            'days': kwargs.get('days'),
            'downloads': kwargs.get('downloads'),
            'notify': kwargs.get('notify')
            }

        res = self.session.post(url=url, params=payload)

        if not res.ok:
            hellraiser(res.json())

        self.transfer_info.update(res.json())

    def delete(self):
        url = getURL('delete')

        payload = {
            'apikey': self.config.get('apikey'),
            'transferid': self.transfer_info.get('transferid'),
            'logintoken': self.config.get('logintoken')
            }

        res = self.session.post(url=url, params=payload)

        if not res.ok:
            hellraiser(res.json())

        print res.json()

    def zip(self):
        url = getURL('zip')

        payload = {
            'apikey': self.config.get('apikey'),
            'transferid': self.transferid,
            'transferkey': self.transfer_info.get('transferkey')
            }

        res = self.session.post(url=url, params=payload)

        if not res.ok:
            hellraiser(res.json())

        print res.json()

    def cancel(self):
        url = getURL('cancel')

        payload = {
            'apikey': self.config.get('apikey'),
            'transferid': self.transferid,
            'transferkey': self.transfer_info.get('transferkey')
            }

        res = self.session.post(url=url, params=payload)

        if not res.ok:
            hellraiser(res.json())

        self._complete = True
        print res.json()

    def share(self, **kwargs):
        url = getURL('share')

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.config.get('logintoken'),
            'transferid': self.transferid,
            'to': ','.join(list(kwargs.get('to'))),
            'from': self.config.get('username'),
            'message': kwargs.get('message')
            }

        res = self.session.post(url=url, params=payload)

        if not res.ok:
            hellraiser(res.json())

        print res.json()

    def forward(self, to=None):
        if isinstance(to, (str, unicode)):
            to = to.split(',')
        elif isinstance(to, list):
            to = ','.join(to)

        url = getURL('forward')

        payload = {
            'apikey': self.config.get('apikey'),
            'transferid': self.transferid,
            'transferkey': self.transfer_info.get('transferkey'),
            'to': to
            }

        res = self.session.post(url=url, params=payload)

        if not res.ok:
            hellraiser(res.json())

        print res.json()

    def getFiles(self):
        url = getURL('get')

        payload = {
            'apikey': self.config.get('apikey'),
            'transferid': self.transferid,
            'logintoken': self.config.get('logintoken')
            }

        res = self.session.post(url=url, params=payload)

        if not res.ok:
            hellraiser(res.json())

        self.transfer_info.update(res.json())
        files = self.transfer_info['transfer']['files']

        #del(self.transfer_info['files'])

        for file_data in files:
            self.addFile(FMFile(data=file_data))

        return self.files()

    def renameFile(self, fmfile, filename):
        if not isinstance(fmfile, FMFile):
            raise FMFileError('fmfile must be an FMFile object')

        url = getURL('file_rename')

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.config.get('logintoken'),
            'fileid': fmfile.get('fileid'),
            'filename': filename
            }

        res = self.session.post(url=url, params=payload)
        if not res.ok:
            hellraiser(res.json())

        self._complete = True
        return res.json()

    def deleteFile(self, fmfile):
        if not isinstance(fmfile, FMFile):
            raise FMFileError('fmfile must be an FMFile object')

        url = getURL('file_delete')

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.config.get('logintoken'),
            'fileid': fmfile.get('fileid')
            }

        res = self.session.post(url=url, params=payload)
        if not res.ok:
            hellraiser(res.json())

        self._complete = True
        return res.json()

    def _initialize(self):
        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.config.get('logintoken'),
            }
        payload.update(self.transfer_info)

        url = getURL('init')

        res = self.session.post(url=url, params=payload)
        if not res.ok:
            hellraiser(res.json())

        return res.json()

    def __repr__(self):
        return repr(self.transfer_info)


class FMFile():

    def __init__(self, fullpath=None, data=None):
        self._file_info = {}
        self.fullpath = fullpath
        self.path = None
        self.filename = None
        self.config = None

        if self.fullpath is not None:
            self.addFile(self.fullpath)

        if data is not None:
            self.updateFileInfo(data)

    def addFile(self, filename):
        if not os.path.isfile(filename):
            raise Exception('No such file: {}'.format(filename))

        self.path, self.filename = os.path.split(filename)

        self.updateFileInfo(self.getFileSpecs())

    def download(self, path):
        pass

    def set(self, key, value):
        self._file_info[key] = value

    def get(self, key):
        if key in self._file_info:
            return self._file_info[key]

        return None

    def updateFileInfo(self, data):
        if not isinstance(data, dict):
            raise Exception('A dict must be passed')

        for key, value in data.items():
            self.set(key, value)

    def fileInfo(self):
        return self._file_info

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
        return repr(self.fileInfo())


class Contacts():

    def __init__(self):
        super(Contacts, self).__init__()


class Company():

    def __init__(self):
        super(Company, self).__init__()