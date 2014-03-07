# -*- coding: utf-8 -*-
import os
import requests
from hashlib import md5
from uuid import uuid4
from mimetypes import guess_type

from config import Config
from errors import *


class Filemail(object):

    def __init__(self):
        self._logged_in = False

        self.fm_config = Config()
        self.fm_user = None
        self.fm_address = self.fm_config['Address']

    def login(self, user):
        self._connection('login', user)
        return self

    def logout(self):
        user = self.fm_user['username']
        self._connection('logout', user)

    def getURL(self, action):
        urls = {
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
            'received_get': 'api/transfer/received/get'
            }

        if action in urls:
            login_url = os.path.join(
                self.fm_address['base_url'],
                urls[action]
            )
            return login_url
        raise FMBaseError('You passed an invalid action: {}'.format(action))

    def _connection(self, action, user):
        if action not in ['login', 'logout']:
            raise FMBaseError('{}, is not a vaid action'.format(action))

        url = self.getURL(action)
        payload = self._getAuthentication(action, user)

        res = requests.post(
            url=url,
            params=payload
            )
        #res_json = res.json()

        #if res_json['responsestatus'] != 'OK':
        if not res:
            self._raiseError(res)

        if action == 'login':
            login_token = res.json()['logintoken']
            self.fm_user['logintoken'] = login_token

        self._logged_in = not self._logged_in

    def _getAuthentication(self, action, user):
        if action not in ['login', 'logout']:
            raise FMBaseError('{}, is not a vaid action'.format(action))

        self.fm_user = self.fm_config[user]
        if not self.fm_user:
            raise FMBaseError('Unknown User: {}'.format(user))

        auth_keys = {
            'login': ['apikey', 'username', 'password', 'source', 'logintoken'],
            'logout': ['apikey', 'logintoken']
            }

        payload = dict(map(lambda k: (k, self.fm_user[k]), auth_keys[action]))

        return payload

    def _raiseError(self, response):
        status_code = response.status_code
        if status_code <= 1999:
            raise FMGenericError(status_code)

    def __getattr__(self, attr):
        if attr in self.fm_user:
            return self.fm_user[attr]
        raise AttributeError('No attribute named: {}'.format(attr))


class Authentication():

    def __init__(self, config):
        super(Authentication, self).__init__()


class Transfer():

    def __init__(self, login, **kwargs):
        self._auth = login
        self._transfer_info = kwargs
        self._transfer_info.update({'from': self._auth.username})

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
        url = self._auth.getURL('complete')

        payload = {
            'apikey': self._auth.apikey,
            'transferid': self.transferid,
            'transferkey': self.transferkey,
            'keep_transfer_key': keep_transfer_key
            }

        res = requests.post(url=url, params=payload)

        if not res.ok:
            print res.json()['errormessage']
        print res.json()

    def get(self):
        url = self._auth.getURL('get')

        payload = {
            'apikey': self._auth.apikey,
            'transferid': self.transferid,
            'logintoken': self._auth.logintoken
            }

        res = requests.post(url=url, params=payload)

        if not res.ok:
            print res.json()['errormessage']
        print res.json()

    def update():
        pass

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
            'apikey': self._auth.apikey,
            'logintoken': self._auth.logintoken,
            }
        payload.update(self._transfer_info)

        url = self._auth.getURL('init')

        res = requests.post(url=url, params=payload)
        if not res:
            raise FMBaseError(res.status_code)

        return res.json()


class User():

    def __init__(self):
        super(User, self).__init__()


class Contacts():

    def __init__(self):
        super(Contacts, self).__init__()


class Company():

    def __init__(self):
        super(Company, self).__init__()