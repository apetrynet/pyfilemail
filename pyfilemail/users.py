"""
filemail.users
~~~~~~~~~~~~~~

Contains :User:, :Contact:, :Group: and :Company: classes
"""

import os
import json
from appdirs import AppDirs
from calendar import timegm
from datetime import datetime, timedelta
from requests import Session

from pyfilemail import logger
from urls import get_URL
from config import Config
from transfer import Transfer
from errors import hellraiser, FMBaseError


class User():
    """
    This is the entry point to filemail. You need a valid user to login.

    :param username: `String` with registered filemail username
    :param apikey: (optional) `String` api key from filemail.com
    :param password: (optional) `String` users filemail password
    :param \*\*kwargs: Additional `key=value` pairs with user setings.
        See :class:`Config` for valid keywords.
    """

    def __init__(self, username, password=None):

        self.username = username
        self._transfers = []

        self.session = Session()
        self.config = self.load_config()

        apikey = self.config.get('apikey')
        self.session.cookies['apikey'] = apikey
        if apikey.startswith('GET KEY FROM'):
            msg = 'No API KEY set in config.\n{apikey}\n'
            logger.warning(msg.format(apikey=apikey))

        if password is not None:
            self.login(password)
            self.session.cookies['source'] = 'Desktop'

        else:
            self.session.cookies['source'] = 'web'
            self.session.cookies['logintoken'] = None

    def load_config(self):
        configfile = self.get_configfile()

        with open(configfile, 'rb') as f:
            return json.load(f)

    def save_config(self, init=False, configfile=None):
        if init:
            data = {
                'apikey': 'GET KEY FROM www.filemail.com/apidoc/ApiKey.aspx'
                }

        else:
            configfile = self.get_configfile()
            data = self.config

        with open(configfile, 'wb') as f:
            json.dump(data, f, indent=2)

    def get_configfile(self):
        ad = AppDirs('pyfilemail')
        configdir = ad.user_data_dir
        configfile = os.path.join(configdir, 'pyfilemail.cfg')

        if not os.path.exists(configfile):
            if not os.path.exists(configdir):
                os.makedirs(configdir)

            self.save_config(init=True, configfile=configfile)

        return configfile

    def addContact(self, name, email):
        """
        :param name: `String` with name of contact
        :param email: `String` with vaild email for contact
        :returns: :class:`Contact` object for new current user
        """

        self.validateLoginStatus()

        if not validString(name):
            raise AttributeError('`name` must be a <str> or <unicode>')

        if not validEmail(email):
            raise AttributeError('Not a valid email')

        method, url = getURL('contacts_add')

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.config.get('logintoken'),
            'name': name,
            'email': email
            }

        res = self.session.send(method=method, url=url, params=payload)

        if not res.ok:
            hellraiser(res.json())

        contact = res.json()['contact']

        return Contact(**contact)

    def deleteContact(self, contact):
        """
        Delete contact.

        :param comtact: :class:`Comtact`
        """

        self.validateLoginStatus()

        if not isinstance(contact, Contact):
            raise AttributeError('contact must be a <Contact> instance')

        method, url = getURL('contacts_delete')

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.config.get('logintoken'),
            'contactid': contact.get('contactid')
            }

        res = self.session.send(method=method, url=url, params=payload)

        if not res.ok:
            hellraiser(res.json())

    def getInfo(self):
        """
        :returns: :class:`Config` object containig user
            information and default settings.
        """

        #: Fail if user not logged in
        self.validateLoginStatus()

        method, url = getURL('user_get')

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.config.get('logintoken')
            }

        res = self.session.send(method=method, url=url, params=payload)

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

        method, url = getURL('user_update')

        res = self.session.send(method=method,
                                url=url,
                                params=self.config.dump())

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

        method, url = getURL('sent_get')

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.config.get('logintoken'),
            'getall': expired
            }

        res = self.session.send(method=method, url=url, params=payload)

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

        method, url = getURL('received_get')

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

        res = self.session.send(method=method, url=url, params=payload)

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

    def getContacts(self):
        """
        :returns: `List` of :class:`Contact` objects for the current user
        """

        self.validateLoginStatus()

        method, url = getURL('contacts_get')

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.config.get('logintoken')
            }

        res = self.session.send(method=method, url=url, params=payload)

        if not res.ok:
            hellraiser(res.json())

        contacts = list()
        for contact in res.json()['contacts']:
            contacts.append(Contact(**contact))
        return contacts

    @property
    def is_anonymous(self):
        return not self.session.cookies.get('logintoken')

    @property
    def logged_in(self):
        return not self.session.cookies.get('logintoken')

    def login(self, password):
        """
        Login to filemail as the current user.
        """

        method, url = get_URL('login')
        payload = {
            'apikey': self.config.get('apikey'),
            'username': self.username,
            'password': password,
            'source': 'Desktop'
            }

        res = getattr(self.session, method)(url, params=payload)

        if res.status_code == 200:
            return True

        hellraiser(res)

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

    def updateContact(self, contact, name=None, email=None):
        """
        Update name and/or email for contact.

        :param contact: :class:`Contact` instance to change
        :param name: `String` with updated name
        :param email: `Stinng` with updated email
        """

        self.validateLoginStatus()

        if not isinstance(contact, Contact):
            raise AttributeError('contact must be a <Contact> instance')

        if name is not None and not validString(name):
            raise AttributeError('`name` must be a <str> or <unicode>')

        if email is not None and not validEmail(email):
            raise AttributeError('Not a valid email')

        method, url = getURL('contacts_update')

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.config.get('logintoken'),
            'contactid': contact.get('contactid'),
            'name': name or contact.get('name'),
            'email': email or contact.get('email')
            }

        res = self.session.send(method=method, url=url, params=payload)

        if not res.ok:
            hellraiser(res.json())

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


class Contact():

    def __init__(self, **kwargs):
        self._data = kwargs

    def get(self, key):
        if key in self._data:
            return self._data[key]

        return None

    def set(self, key, value):
        self._data[key] = value

    def __repr__(self):
        return repr(self._data)


class Group():

    def __init__(self, **kwargs):
        self._data = kwargs

    def get(self, key):
        if key in self._data:
            return self._data[key]

        return None

    def set(self, key, value):
        self._data[key] = value

    def __repr__(self):
        return repr(self._data)


class Company():

    def __init__(self):
        raise NotImplemented