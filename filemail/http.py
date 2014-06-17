from requests import Session

from urls import getURL
from errors import hellraiser, FMBaseError


class FMConnection():
    '''Handles all communication with Filemail.com'''

    def __init__(self, user):
        self._user = user
        self._config = self._user.getConfig()
        self._session = Session()
        self._logged_in = False

    def login(self):
        self._connect('login')
        return True

    def logout(self):
        self._connect('logout')
        self._session.close()
        return True

    def post(self, url=None, params=None, **kwargs):
        res = self._session.post(url=url, params=params, **kwargs)
        return res

    def _connect(self, action):
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