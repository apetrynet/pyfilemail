import os
import json
from appdirs import AppDirs
from calendar import timegm
from datetime import datetime, timedelta
from requests import Session

from pyfilemail import logger
from urls import get_URL
from transfer import Transfer
from errors import hellraiser, FMBaseError


class User():
    """
    This is the entry point to filemail. If you use a registered username you'll
    need to provide a password to login.

    :param username: your email/username
    :param password: filename password if registered username is used
    :type username: str
    :type password: str
    """

    def __init__(self, username, password=None):

        self.username = username
        self.transfers = []

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
        """Load configuration file containing API KEY and other settings.
        :rtype: str
        """

        configfile = self.get_configfile()

        if not os.path.exists(configfile):
            self.save_config()

        with open(configfile, 'rb') as f:
            return json.load(f)

    def save_config(self):
        """Save configuration file to users data location.

         - Linux: ~/.local/share/pyfilemail
         - OSX: ~/Library/Application Support/pyfilemail
         - Windows: C:\\\Users\\\{username}\\\AppData\\\Local\\\pyfilemail

         :rtype: str
        """

        configfile = self.get_configfile()

        if not os.path.exists(configfile):
            configdir = os.path.dirname(configfile)

            if not os.path.exists(configdir):
                os.makedirs(configdir)

            data = {
                'apikey': 'GET KEY FROM www.filemail.com/apidoc/ApiKey.aspx'
                }

        else:
            data = self.config

        with open(configfile, 'wb') as f:
            json.dump(data, f, indent=2)

    def get_configfile(self):
        """Return full path to configuration file.

         - Linux: ~/.local/share/pyfilemail
         - OSX: ~/Library/Application Support/pyfilemail
         - Windows: C:\\\Users\\\{username}\\\AppData\\\Local\\\pyfilemail

         :rtype: str
        """

        ad = AppDirs('pyfilemail')
        configdir = ad.user_data_dir
        configfile = os.path.join(configdir, 'pyfilemail.cfg')

        return configfile

    @property
    def is_anonymous(self):
        """:returns: If user is a registered user or not.
        :rtype: bool
        """

        return not self.session.cookies.get('logintoken')

    @property
    def logged_in(self):
        """:returns: If registered user is logged in or not.
        :rtype: bool
        """
        return self.session.cookies.get('logintoken') and True or False

    def login(self, password):
        """Login to filemail as the current user.
        :param password:
        :type password: str
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

    def get_sent(self, expired=False, for_all=False):
        """Retreve information on previously sent transfers.

        :param expired: Whether or not to return expired transfers.
        :param for_all: Get transfers for all users.
         Requires a Filemail Business account.
        :type for_all: bool
        :type expired: bool
        :rtype: ``list`` of :class:`pyfilemail.Transfer` objects
        """

        if not self.logged_in:
            raise FMBaseError('Please login to use this method')

        method, url = get_URL('get_sent')

        payload = {
            'apikey': self.session.cookies.get('apikey'),
            'logintoken': self.session.cookies.get('logintoken'),
            'getexpired': expired,
            'getforallusers': for_all
            }

        res = getattr(self.session, method)(url, params=payload)

        if res.status_code == 200:
            transfers = []
            for transfer_data in res.json()['transfers']:
                user = transfer_data['from']
                if user == self.username:
                    user = self

                transfer = Transfer(user, _restore=True)
                transfer.transfer_info.update(transfer_data)
                transfer.get_files()
                transfers.append(transfer)

            return transfers

        hellraiser(res.json())

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

    def logout(self):
        """Logout of filemail and closing the session."""

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

        for transfer in self.transfers:
            if not transfer.isComplete():
                error = {
                    'errorcode': 4003,
                    'errormessage': 'You must complete transfer before logout.'
                    }
                hellraiser(error)


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
