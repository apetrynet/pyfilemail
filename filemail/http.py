from requests import Session

from urls import getURL
from errors import hellraiser, FMBaseError


class FMConnection():
    """
    Initializes and maintains the connection to filemail.

    :param user: :class:`User` registered with filemail
    """

    def __init__(self, user):
        self._user = user
        self._config = self._user.getConfig()
        self._session = Session()
        self._logged_in = False

    def login(self):
        """
        Login as inited user.

        :returns: `Boolean` with success or not
        """

        self._connect('login')
        return True

    def logout(self):
        """
        Logout as inited user.

        :returns: `Boolean` with success or not
        """

        self._connect('logout')
        self._session.close()
        return True

    def post(self, url=None, params=None, **kwargs):
        """
        HTTP POST

        :param url: `String` to filemail
        :param params: `Dictionary` with payload from all functions
        :param \*\*kwargs: with additional data for transfers

        """

        res = self._session.post(url=url, params=params, **kwargs)
        return res

    def _connect(self, action):
        """
        Connect and Disconnect to filemail.

        :param action: `String` 'login' or 'logout'

        """

        if action not in ['login', 'logout']:
            raise FMBaseError('{}, is not a vaid action'.format(action))

        url = getURL(action)
        auth_keys = {
            'login': ['apikey', 'username', 'password', 'source', 'logintoken'],
            'logout': ['apikey', 'logintoken']
            }

        payload = map(lambda k: (k, self._config.get(k)), auth_keys[action])

        res = self.post(url=url,
                        params=dict(payload))

        if not res.ok:
            self._session.close()
            hellraiser(res.json())

        if action == 'login':
            login_token = res.json()['logintoken']
            self._config.set('logintoken', login_token)

        self._logged_in = not self._logged_in

    def __del__(self):
        self._session.close()