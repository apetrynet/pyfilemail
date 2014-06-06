import os
from errors import FMConfigError


base_url = 'https://www.filemail.com'

api_urls = {
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
    'received_get': 'api/transfer/received/get',
    'user_get': 'api/user/get',
    'user_update': 'api/user/update'
    }


def getURL(action):
    if action in api_urls:
        url = os.path.join(base_url, api_urls[action])
        return url

    raise FMConfigError('You passed an invalid action: {}'.format(action))
