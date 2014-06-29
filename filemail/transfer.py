import os

from urls import getURL
from fmfile import FMFile
from errors import hellraiser, FMBaseError, FMFileError


class Transfer():
    """
    The Transfer object is the gateway to sending and recieving files through
    filemail.com.

    :param user: :ref:`User` object with valid login status
    :param \*\*kwargs: (optional) additional arguments for the transfer like:
        `to` (recipient), `subject`, `message`, `signature`, `notification`
        and so on.
        See the `filemail API <http://www.filemail.com/apidoc/Transfer.aspx>`_
        for more info.

    Recipient(s) and other info can be updated with the :ref:`update` method at
    a later stage.
    """

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