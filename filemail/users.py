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
    """
    This is the entry point to filemail. You need a valid user to login.

    :param username: `String` with registered filemail username
    :param apikey: (optional) `String` api key from filemail.com
    :param password: (optional) `String` users filemail password
    :param \*\*kwargs: Additional `key=value` pairs with user setings
    """

    def __init__(self, username, apikey=None, password=None, **kwargs):

        self._logged_in = False
        self._transfers = []
        self.username = username

        self.config = Config(self.username)
        self.config.load()

        if apikey and password:
            self.config.set('apikey', apikey)
            self.config.set('password', password)

        if kwargs:
            for key, value in kwargs.items():
                self.config.set(key, value)

        self.session = FMConnection(self)

    def getInfo(self):
        """
        :returns: :class:`Config` object containig user
            information and default settings.
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

    def updateUserInfo(self, info=None):
        """
        Update user information and settings.

        :param info: (optional) `Dictionary` or :class:`Config` object
            containing information.

        If no info is passed the current config is sent.

        """

        self.validateLoginStatus()

        if info is not None:
            if isinstance(info, Config):
                info = info.dump()

            self.config.update(info)

        url = getURL('user_update')

        res = self.session.post(url=url, params=self.config.dump())

        if not res.ok:
            hellraiser(res.json())

    def getSent(self, expired=False):
        """
        Retreve information on previously sent transfers.

        :param expired: `Boolean` setting whether or not to return expired
            transfers.
        :returns: `List` with :class:`Transfer` objects
        """
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
        """
        This is used to retrieve a list of transfers sent to you or your company
        from other people.

        :param age: `Integer` between 1 and 90 days.
        :param for_all: `Boolean` if ``True`` will return received files for
            all users in the same business. (Available for business account
            members only).
        :returns: List of :class:`Transfer` objects.

        Retrieving files is only available for users with an
        `business account <http://www.filemail.com>`_.

        """
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

        transfers = list()
        for transfer in res.json()['transfers']:
            transfers.append(Transfer(self, **transfer))
        return transfers

    def getConfig(self):
        """
        :returns: The users current :class:`Config` object.
        """

        return self.config

    def save(self, config_path=None):
        """
        Saves the current config/settings to `config_path`.

        :param config_path: (optional) `String` with fullpath to
            ``filemail.cfg``.

        If `config_path` is ``None`` it defaults to ``${HOME}/filemail.cfg``.
        """

        self.config.save(config_path)

    def login(self):
        """
        Login to filemail as the current user.
        """

        state = self.session.login()
        self._setLoginState(state)

    def logout(self):
        """
        Logout of filemail and closing the session.
        """

        self.checkAllTransfers()

        state = self.session.logout()
        self._setLoginState(state)

    def validateLoginStatus(self):
        """
        Check if user is propperly loged in.
        """

        if self._logged_in:
            return True

        raise FMBaseError('You must be logged in')

    def addTransfer(self, transfer):
        """
        Add a :class:`Transfer` to an internal list of transfers associated
        with the users current session.

        :param transfer: :class:`Transfer` object
        """

        if transfer not in self._transfers:
            self._transfers.append(transfer)

    def transfers(self):
        """
        :returns: `List` of :class:`Transfer` objects.
        """

        return self._transfers

    def checkAllTransfers(self):
        """
        Check if all transfers are completed.
        """

        for transfer in self.transfers():
            if not transfer.isComplete():
                error = {
                    'errorcode': 4003,
                    'errormessage': 'You must complete transfer before logout.'
                    }
                hellraiser(error)

    def _setLoginState(self, state):
        """
        Set login state to ``True`` or ``False``
        """

        self._logged_in = state


class Contacts():

    def __init__(self):
        raise NotImplemented


class Company():

    def __init__(self):
        raise NotImplemented
