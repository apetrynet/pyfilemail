from calendar import timegm
from datetime import datetime, timedelta
from requests import Session

import pyfilemail as pm
from pyfilemail import logger, login_required, load_config, get_configfile
from urls import get_URL
from transfer import Transfer
from errors import hellraiser, FMBaseError


class User(object):
    """This is the entry point to filemail.
    If you use a registered username you'll need to provide
    a password to login. If no password is passed during init a search for
    password is done in $HOME/.netrc
    You may also login at a later time with the :func:`User.login` function.

    :param username: your email/username
    :param password: filemail password if registered username is used
    :type username: str
    :type password: str

    ::

        #$HOME/.netrc example:
        machine yourfilemailuser@email.com
                login yourfilemailuser@email.com
                password topsecretpassword

    """

    def __init__(self, username, password=None):

        self.username = username
        self.transfers = []

        self.session = Session()
        self.session.cookies['source'] = 'Desktop'
        self.config = load_config()

        apikey = self.config.get('apikey')
        self.session.cookies['apikey'] = apikey
        if apikey.startswith('GET KEY AT:'):
            msg = 'No API KEY set in {conf}.\n{apikey}\n'
            logger.warning(msg.format(conf=get_configfile(), apikey=apikey))

        if password is None and pm.NETRC:
            machine = pm._netrc.authenticators(username)
            if machine:
                password = machine[2]

            else:
                password = None

        if password is not None:
            self.login(password)

        else:
            self.session.cookies['logintoken'] = None

    @property
    def is_registered(self):
        """If user is a registered user or not.

        :rtype: bool
        """

        return not self.session.cookies.get('logintoken')

    @property
    def logged_in(self):
        """If registered user is logged in or not.

        :rtype: bool
        """
        return self.session.cookies.get('logintoken') and True or False

    def login(self, password):
        """Login to filemail as the current user.

        :param password:
        :type password: ``str``
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

    @login_required
    def logout(self):
        """Logout of filemail and closing the session."""

        # Check if all transfers are complete before logout
        self.transfers_complete

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.session.cookies.get('logintoken')
            }

        method, url = get_URL('logout')
        res = getattr(self.session, method)(url, params=payload)

        if res.status_code == 200:
            self.session.cookies['logintoken'] = None
            return True

        hellraiser(res)

    @property
    def transfers_complete(self):
        """Check if all transfers are completed."""

        for transfer in self.transfers:
            if not transfer.is_complete:
                error = {
                    'errorcode': 4003,
                    'errormessage': 'You must complete transfer before logout.'
                    }
                hellraiser(error)

    @login_required
    def get_sent(self, expired=False, for_all=False):
        """Retreve information on previously sent transfers.

        :param expired: Whether or not to return expired transfers.
        :param for_all: Get transfers for all users.
         Requires a Filemail Business account.
        :type for_all: bool
        :type expired: bool
        :rtype: ``list`` of :class:`pyfilemail.Transfer` objects
        """

        method, url = get_URL('get_sent')

        payload = {
            'apikey': self.session.cookies.get('apikey'),
            'logintoken': self.session.cookies.get('logintoken'),
            'getexpired': expired,
            'getforallusers': for_all
            }

        res = getattr(self.session, method)(url, params=payload)

        if res.status_code == 200:
            return self._restore_transfers(res)

        hellraiser(res.json())

    @login_required
    def get_user_info(self, save_to_config=True):
        """Get user info and settings from Filemail.

        :param save_to_config: Whether or not to save settings to config file
        :type save_to_config: ``bool``
        :rtype: ``dict`` containig user information and default settings.
        """

        method, url = get_URL('user_get')

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.session.cookies.get('logintoken')
            }

        res = getattr(self.session, method)(url, params=payload)

        if res.status_code == 200:
            settings = res.json()['user']

            if save_to_config:
                self.config.update(settings)

            return settings

        hellraiser(res)

    @login_required
    def update_user_info(self, **kwargs):
        """Update user info and settings.

        :param \*\*kwargs: settings to be merged with
         :func:`User.get_configfile` setings and sent to Filemail.
        :rtype: ``bool``
        """

        if kwargs:
            self.config.update(kwargs)

        method, url = get_URL('user_update')

        res = getattr(self.session, method)(url, params=self.config)

        if res.status_code == 200:
            return True

        hellraiser(res)

    @login_required
    def get_received(self, age=None, for_all=True):
        """Retrieve a list of transfers sent to you or your company
         from other people.

        :param age: between 1 and 90 days.
        :param for_all: If ``True`` will return received files for
         all users in the same business. (Available for business account
         members only).
        :type age: ``int``
        :type for_all: ``bool``
        :rtype: ``list`` of :class:`Transfer` objects.
        """

        method, url = get_URL('received_get')

        if age:
            if not isinstance(age, int) or age < 0 or age > 90:
                raise FMBaseError('Age must be <int> between 0-90')

            past = datetime.utcnow() - timedelta(days=age)
            age = timegm(past.utctimetuple())

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.session.cookies.get('logintoken'),
            'getForAllUsers': for_all,
            'from': age
            }

        res = getattr(self.session, method)(url, params=payload)

        if res.status_code == 200:
            return self._restore_transfers(res)

        hellraiser(res)

    def _restore_transfers(self, response):
        """Restore transfers from josn retreived Filemail
        :param response: response object from request
        :rtype: ``list`` with :class:`Transfer` objects
        """

        transfers = []
        for transfer_data in response.json()['transfers']:
            transfer = Transfer(self, _restore=True)
            transfer.transfer_info.update(transfer_data)
            transfer.get_files()
            transfers.append(transfer)

        return transfers

    @login_required
    def get_contacts(self):
        """Get contacts from Filemail. Usually people you've sent files
         to in the past.

        :rtype: ``list`` of ``dict`` objects containing contact information
        """

        method, url = get_URL('contacts_get')

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.session.cookies.get('logintoken')
            }

        res = getattr(self.session, method)(url, params=payload)

        if res.status_code == 200:
            return res.json()['contacts']

        hellraiser(res)

    @login_required
    def get_contact(self, email):
        """Get Filemail contact based on email.

        :param email: address of contact
        :type email: ``str``, ``unicode``
        :rtype: ``dict`` with contact information
        """

        contacts = self.get_contacts()
        for contact in contacts:
            if contact['email'] == email:
                return contact

        msg = 'No contact with email: "{email}" found.'
        raise FMBaseError(msg.format(email=email))

    @login_required
    def update_contact(self, contact):
        """Update name and/or email for contact.

        :param contact: with updated info
        :type contact: ``dict``
        :rtype: ``bool``
        """

        if not isinstance(contact, dict):
            raise AttributeError('contact must be a <dict>')

        method, url = get_URL('contacts_update')

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.session.cookies.get('logintoken'),
            'contactid': contact.get('contactid'),
            'name': contact.get('name'),
            'email': contact.get('email')
            }

        res = getattr(self.session, method)(url, params=payload)

        if res.status_code == 200:
            return True

        hellraiser(res)

    @login_required
    def add_contact(self, name, email):
        """Add new contact.

        :param name: name of contact
        :param email: email of contact
        :type name: ``str``, ``unicode``
        :type email: ``str``, ``unicode``
        :returns: contact information for new current user
        :rtype: ``dict``
        """

        method, url = get_URL('contacts_add')

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.session.cookies.get('logintoken'),
            'name': name,
            'email': email
            }

        res = getattr(self.session, method)(url, params=payload)

        if res.status_code == 200:
            return res.json()['contact']

        hellraiser(res)

    @login_required
    def delete_contact(self, contact):
        """Delete contact.

        :param contact: with `contactid`
        :type contact: ``dict``
        :rtype: ``bool``
        """

        if not isinstance(contact, dict):
            raise AttributeError('contact must be a <dict>')

        method, url = get_URL('contacts_delete')

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.session.cookies.get('logintoken'),
            'contactid': contact.get('contactid')
            }

        res = getattr(self.session, method)(url, params=payload)

        if res.status_code == 200:
            return True

        hellraiser(res)

    @login_required
    def get_groups(self):
        """Get contact groups

        :rtype: ``list`` of ``dict`` with group data
        """

        method, url = get_URL('groups_get')

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.session.cookies.get('logintoken')
            }

        res = getattr(self.session, method)(url, params=payload)

        if res.status_code == 200:
            return res.json()['groups']

        hellraiser(res)

    @login_required
    def get_group(self, name):
        """Get contact group by name

        :param name: name of group
        :type name: ``str``, ``unicode``
        :rtype: ``dict`` with group data
        """

        groups = self.get_groups()
        for group in groups:
            if group['contactgroupname'] == name:
                return group

        msg = 'No group named: "{name}" found.'
        raise FMBaseError(msg.format(name=name))

    @login_required
    def add_group(self, name):
        """Add new contact group

        :param name: name of new group
        :type name: ``str``, ``unicode``
        :rtype: ``dict`` with group data
        """

        method, url = get_URL('group_add')

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.session.cookies.get('logintoken'),
            'name': name
            }

        res = getattr(self.session, method)(url, params=payload)

        if res.status_code == 200:
            return res.json()['groups']

        hellraiser(res)

    @login_required
    def delete_group(self, name):
        """Delete contact group

        :param name: of group
        :type name: ``str``, ``unicode``
        :rtype: ``bool``
        """

        group = self.get_group(name)

        method, url = get_URL('group_delete')

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.session.cookies.get('logintoken'),
            'contactgroupid': group['contactgroupid']
            }

        res = getattr(self.session, method)(url, params=payload)

        if res.status_code == 200:
            return True

        hellraiser(res)

    @login_required
    def rename_group(self, group, newname):
        """Rename contact group

        :param group: group data or name of group
        :param newname: of group
        :type group: ``str``, ``unicode``, ``dict``
        :type newname: ``str``, ``unicode``
        :rtype: ``bool``
        """

        if isinstance(group, basestring):
            group = self.get_contact(group)

        method, url = get_URL('group_update')

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.session.cookies.get('logintoken'),
            'contactgroupid': group['contactgroupid'],
            'name': newname
            }

        res = getattr(self.session, method)(url, params=payload)

        if res.status_code == 200:
            return True

        hellraiser(res)

    @login_required
    def add_contact_to_group(self, contact, group):
        """Add contact to group

        :param contact: name or contact object
        :param group: name or group object
        :type contact: ``str``, ``unicode``, ``dict``
        :type group: ``str``, ``unicode``, ``dict``
        :rtype: ``bool``
        """

        if isinstance(contact, basestring):
            contact = self.get_contact(contact)

        if isinstance(group, basestring):
            group = self.get_group(group)

        method, url = get_URL('contacts_add_to_group')

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.session.cookies.get('logintoken'),
            'contactid': contact['contactid'],
            'contactgroupid': group['contactgroupid']
            }

        res = getattr(self.session, method)(url, params=payload)

        if res.status_code == 200:
            return True

        hellraiser(res)

    @login_required
    def remove_contact_from_group(self, contact, group):
        """Remove contact from group

        :param contact: name or contact object
        :param group: name or group object
        :type contact: ``str``, ``unicode``, ``dict``
        :type group: ``str``, ``unicode``, ``dict``
        :rtype: ``bool``
        """

        if isinstance(contact, basestring):
            contact = self.get_contact(contact)

        if isinstance(group, basestring):
            group = self.get_group(group)

        method, url = get_URL('contacts_remove_from_group')

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.session.cookies.get('logintoken'),
            'contactid': contact['contactid'],
            'contactgroupid': group['contactgroupid']
            }

        res = getattr(self.session, method)(url, params=payload)

        if res.status_code == 200:
            return True

        hellraiser(res)

    @login_required
    def get_company_info(self):
        """Get company settings from Filemail

        :rtype: ``dict`` with company data
        """

        method, url = get_URL('company_get')

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.session.cookies.get('logintoken')
            }

        res = getattr(self.session, method)(url, params=payload)

        if res.status_code == 200:
            return res.json()['company']

        hellraiser(res)

    @login_required
    def update_company(self, company):
        """Update company settings

        :param company: updated settings
        :type company: ``dict``
        :rtype: ``bool``
        """

        if not isinstance(company, dict):
            raise AttributeError('company must be a <dict>')

        method, url = get_URL('company_update')

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.session.cookies.get('logintoken')
            }

        payload.update(company)

        res = getattr(self.session, method)(url, params=payload)

        if res.status_code == 200:
            return True

        hellraiser(res)

    @login_required
    def get_company_users(self):
        """Get company users from Filemail

        :rtype: ``list`` of ``dict`` with user data
        """

        method, url = get_URL('company_get_users')

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.session.cookies.get('logintoken')
            }

        res = getattr(self.session, method)(url, params=payload)

        if res.status_code == 200:
            return res.json()['users']

        hellraiser(res)

    @login_required
    def get_company_user(self, email):
        """Get company user based on email.

        :param email: address of contact
        :type email: ``str``, ``unicode``
        :rtype: ``dict`` with contact information
        """

        users = self.get_company_users()
        for user in users:
            if user['email'] == email:
                return user

        msg = 'No user with email: "{email}" associated with this company.'
        raise FMBaseError(msg.format(email=email))

    @login_required
    def company_add_user(self, email, name, password, receiver, admin):
        """Add a user to the company account.

        :param email:
        :param name:
        :param password: Pass without storing in plain text
        :param receiver: Can user receive files
        :param admin:
        :type email: ``str`` or ``unicode``
        :type name: ``str`` or ``unicode``
        :type password: ``str`` or ``unicode``
        :type receiver: ``bool``
        :type admin: ``bool``
        :rtype: ``bool``
        """

        method, url = get_URL('company_add_user')

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.session.cookies.get('logintoken'),
            'email': email,
            'name': name,
            'password': password,
            'canreceivefiles': receiver,
            'admin': admin
            }

        res = getattr(self.session, method)(url, params=payload)

        if res.status_code == 200:
            return True

        hellraiser(res)

    @login_required
    def update_company_user(self, email, userdata):
        """Update a company users settings

        :param email: current email address of user
        :param userdata: updated settings
        :type email: ``str`` or ``unicode``
        :type userdata: ``dict``
        :rtype: ``bool``
        """

        if not isinstance(userdata, dict):
            raise AttributeError('userdata must be a <dict>')

        method, url = get_URL('company_update_user')

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.session.cookies.get('logintoken'),
            'useremail': email
            }

        payload.update(userdata)

        res = getattr(self.session, method)(url, params=payload)

        if res.status_code == 200:
            return True

        hellraiser(res)