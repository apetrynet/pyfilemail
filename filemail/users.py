"""
filemail.users
~~~~~~~~~~~~~~

Contains :User:, :Contacts: and :Company: classes
"""

from calendar import timegm
from datetime import datetime, timedelta

from urls import getURL
from config import Config
from transfer import Transfer
from http import FMConnection
from errors import hellraiser, FMBaseError


class User():
    """This is the entry point to filemail. You need a valid user to login.

    :param username: (optional) String with registered email address
    :param apikey: (optional) String api key from filemail.com
    :param password: (optional) String users filemail password

    """

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
        """:returns: :class:`Config <Config>` object containig user information
        and default settings.
        """

        #: Fail if user not logged in
        self.validateLoginStatus()

        url = getURL('user_get')

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.config.get('logintoken')
            }

        res = self.session.post(url=url, params=payload)

        if not res.ok:
            hellraiser(res.json())

        return Config(self.username, **res.json()['user'])

    def updateUserInfo(self, info):
        """Update user information and settings.

        :param info: Dictionary containing information"""

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


class Contacts():

    def __init__(self):
        raise NotImplemented


class Company():

    def __init__(self):
        raise NotImplemented
