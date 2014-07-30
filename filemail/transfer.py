import os

from urls import getURL
from fmfile import FMFile
from errors import hellraiser, FMBaseError, FMFileError


class Transfer():
    """
    The Transfer object is the gateway to sending and recieving files through
    filemail.com.

    :param user: `User` object with valid login status
    :param \*\*kwargs: (optional) additional arguments for the transfer.

    `\*\*kwargs` may contain:
        * `to` (email/username)
        * `subject`
        * `message`
        * `signature`
        * `notify` (`Boolean` notify when recipients download files)
        * `confirmation` (`Boolean` confirm when finished uploading)
        * `days` (`Int` days available for download)
        * `password` (for recipients to enter for download access)

    Recipient(s) and other info can be updated with the :func:`update` method at
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
        """
        Add a single file to Transfer.

        :param filename: `String` with full path to file
        """

        if isinstance(filename, FMFile):
            fmfile = filename
        else:
            if not os.path.isfile(filename):
                raise FMBaseError('No such file: {}'.format(filename))

            fmfile = FMFile(filename)

        self._files.append(fmfile)

        self._complete = self.transfer_info.get('status') == 'STATUS_COMPLETE'

    def addFiles(self, files):
        """
        Add multiple files.

        :param files: `List` of paths to files
        """

        for filename in files:
            self.addFile(filename)

    def files(self):
        """:returns: `List` of files related to Transfer"""

        return self._files

    def download(self, files, destination):
        """
        Download file or files from transfer

        :param files: :class:`FMFile` or list of :class:`FMFile`'s
        :param destination: `String` containing save path
        """

        if not isinstance(files, list):
            files = [files]

        for f in files:
            if not isinstance(f, FMFile):
                raise FMFileError('File must be an FMFile instance')

            self._download(f, destination)

    def _download(self, fmfile, destination):
        filename = fmfile.get('filename')
        fullpath = os.path.join(destination, filename)
        chunksize = 65536

        url = fmfile.get('downloadurl')
        stream = self.session.post(url, stream=True)

        with open(fullpath, 'wb') as f:
            for chunk in stream.iter_content(chunksize):
                f.write(chunk)

    def getTransferID(self):
        """
        Get the transfer id for the current Transfer.

        :returns: `String` with transfer id
        """

        if 'transferid' in self.transfer_info:
            transferid = self.transfer_info.get('transferid')
        else:
            transferid = self.transfer_info.get('id')

        return transferid

    def send(self, callback=None, auto_complete=True):
        """
        Begin uploading file(s) and sending email(s).

        :param callback: pass name of callback function that will receive a
            percentage of file transfered
        :param auto_complete: `Boolean` settinng wheter or not to auto complete
            transfer after upload.

        If `auto_complete` is set to ``False`` you will have to call the
        :func:`complete` function
        at a later stage.
        """

        url = self.transfer_info.get('transferurl')

        for fmfile in self._files:
            fmfile.set('transferid', self.transferid)
            fmfile.set('transferkey', self.transfer_info['transferkey'])

            res = self.session.post(url=url,
                                    params=fmfile.fileInfo(),
                                    data=self._fileStreamer(fmfile,
                                                           callback),
                                    stream=True)

            res.text

            if not res.ok:
                hellraiser(res.json())

        if auto_complete:
            self.complete(keep_transfer_key=True)

    def _fileStreamer(self, fmfile, callback=None):
        """
        Supplies the :func:`send` function with bytes of data.

        :param fmfile: :class:`FMFile` object passed from :func:`send`
        :param callback: passed from :func:`send`
        """

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
        """
        Completes the transfer and shoots off email(s) to recipients.

        :param keep_transfer_key: `Boolean` setting whether or not to keep the
            transfer key. This is needed for the :func:`update`
        """

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

    def isComplete(self):
        """:returns: `Boolean` `True` if transfer is complete"""

        return self._complete

    def update(self, **kwargs):
        """
        Update a completed transfer with new information.

        :param \*\*kwargs:

        \*\*kwargs may contain:
            * `message` (`String`)
            * `days` (`Integer`) available
            * `downloads` (`Integer`) number of
            * `notify` (`Boolean`) on downloads
        """

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
        """
        Delete the current transfer.
        """

        url = getURL('delete')

        payload = {
            'apikey': self.config.get('apikey'),
            'transferid': self.transfer_info.get('transferid'),
            'logintoken': self.config.get('logintoken')
            }

        res = self.session.post(url=url, params=payload)

        if not res.ok:
            hellraiser(res.json())

    def zip(self):
        """
        Zip the current transfer on the server side.
        """

        url = getURL('zip')

        payload = {
            'apikey': self.config.get('apikey'),
            'transferid': self.transferid,
            'transferkey': self.transfer_info.get('transferkey')
            }

        res = self.session.post(url=url, params=payload)

        if not res.ok:
            hellraiser(res.json())

    def cancel(self):
        """
        Cancel the current transfer.
        """

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

    def share(self, **kwargs):
        """
        Share the transfer with new message to new people.

        :param \*\*kwargs:

        \*\*kwargs may contain:
            * `to` (`List`) of email addresses or comma seperated `String`
            * `from` (`String`) with alternate email
            * `message` (`String`)
        """

        url = getURL('share')

        if 'to' in kwargs:
            to = kwargs.get('to')
            if isinstance(to, list):
                recipients = ','.join(to)
            else:
                recipients = to

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.config.get('logintoken'),
            'transferid': self.transferid,
            'to': ','.join(recipients),
            'from': kwargs.get('from', self.config.get('username')),
            'message': kwargs.get('message')
            }

        res = self.session.post(url=url, params=payload)

        if not res.ok:
            hellraiser(res.json())

    def forward(self, to=None):
        """
        Forward original transfer to new recipients.

        :param to: `List` of new recipients or comma seperted `String`

        """

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

    def getFiles(self):
        """
        Get `List` of :class:`FMFile` objects for the current transfer.

        :returns: `List` of :class:`FMFile` objects

        """

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

        for file_data in files:
            self.addFile(FMFile(data=file_data))

        return self.files()

    def renameFile(self, fmfile, filename):
        """
        Rename file in transfer.

        :param fmfile: :class:`FMFile` object instance to rename
        :param filename: `String` new filename

        """

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

    def deleteFile(self, fmfile):
        """
        Delete file in transfer.

        :param fmfile: :class:`FMFile` object instance to delete

        """

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

    def _initialize(self):
        """Initialize transfer."""

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.config.get('logintoken'),
            }
        payload.update(self.transfer_info)

        url = getURL('init')

        res = self.session.post(url=url, params=payload)
        if not res.ok:
            hellraiser(res.json())

        print res.json()
        return res.json()

    def __repr__(self):
        return repr(self.transfer_info)