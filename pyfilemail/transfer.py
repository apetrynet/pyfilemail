import os
import datetime
from hashlib import md5
from uuid import uuid4
from mimetypes import guess_type
from zipfile import ZipFile

import users
from pyfilemail import logger
from urls import get_URL
from fmfile import FMFile
from errors import hellraiser, FMBaseError, FMFileError


class Transfer(object):
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

    def __init__(self,
                 fm_user,
                 to=None,
                 subject=None,
                 message=None,
                 notify=False,
                 confirmation=False,
                 days=3,
                 password=None,
                 checksum=True,
                 compress=False):

        if isinstance(fm_user, basestring):
            self.fm_user = users.User(fm_user)

        elif isinstance(fm_user, users.User):
            self.fm_user = fm_user

        else:
            raise FMBaseError('fm_user must be of type "string or User"')

        self.transfer_info = {
            'from': self.fm_user.username,
            'to': self._parse_recipients(to),
            'subject': subject,
            'message': message,
            'notify': notify,
            'confirmation': confirmation,
            'days': days,
            'password': password
            }

        self._files = []
        self._complete = False
        self.checksum = checksum
        self.compress = compress
        self.config = self.fm_user.config
        self.session = self.fm_user.session
        self._initialize()

        #if 'status' not in self.transfer_info:
            #self.transfer_info.update(self._initialize())

        #self.transferid = self.getTransferID()

    def _parse_recipients(self, to):
        if to is None:
            return None

        if isinstance(to, list):
            recipients = []

            for recipient in to:
                if isinstance(recipient, users.Contact):
                    recipients.append(recipient.get('name'))

                elif isinstance(recipient, users.Group):
                    msg = 'Groups are not supported recipients yet. Sorry'
                    raise NotImplemented(msg)

                else:
                    recipients.append(recipient)

        elif isinstance(to, basestring):
            if ',' in to:
                recipients = to.strip().split(',')

            else:
                recipients = [to]

        return ', '.join(recipients)

    def add_files(self, files):
        """
        Add multiple files.

        :param files: `List` of paths to files
        """

        if isinstance(files, basestring):
            files = [files]

        zip_file = None
        if self.compress:
            zip_filename = self._get_zip_filename()
            zip_file = ZipFile(zip_filename, 'w')

        for filename in files:
            if os.path.isdir(filename):
                for dirname, subdirs, filelist in os.walk(filename):
                    if dirname:
                        if self.compress:
                            zip_file.write(dirname)

                    for fname in filelist:
                        filepath = os.path.join(dirname, fname)
                        if self.compress:
                            zip_file.write(filepath)

                        else:
                            fmfile = self.get_file_specs(filepath,
                                                         keep_folders=True)
                            if fmfile['totalzize'] > 0:
                                self._files.append(fmfile)

            else:
                if self.compress:
                    zip_file.write(filename)

                else:
                    fmfile = self.get_file_specs(filename)
                    self._files.append(fmfile)

        if self.compress:
            zip_file.close()
            filename = zip_filename
            fmfile = self.get_file_specs(filename)
            self._files.append(fmfile)

    @property
    def files(self):
        """:returns: `List` of files related to Transfer"""

        return self._files

    def get_file_specs(self, filepath, keep_folders=False):
        path, filename = os.path.split(filepath)

        fileid = str(uuid4()).replace('-', '')

        if self.checksum:
            with open(filepath, 'rb') as f:
                md5hash = md5(f.read()).digest().encode('base64')[:-1]
        else:
            md5hash = None

        specs = {
            'transferid': self.transfer_info['transferid'],
            'transferkey': self.transfer_info['transferkey'],
            'fileid': fileid,
            'filepath': filepath,
            'thefilename': keep_folders and filepath or filename,
            'totalsize': os.path.getsize(filepath),
            'md5': md5hash,
            'content-type': guess_type(filepath)[0]
            }

        return specs

    def _get_zip_filename(self):
        date = datetime.datetime.now().strftime('%Y_%m_%d-%H%M%S')
        zip_file = 'filemail_transfer_{date}.zip'.format(date=date)

        return zip_file

    def download(self, files, destination, callback=None):
        """
        Download file or files.

        :param files: :class:`FMFile` or list of :class:`FMFile`'s
        :param destination: `String` containing save path
        :param callback: pass instance of callback function that will receive a
            percentage of file transfered
        """

        if not isinstance(files, list):
            files = [files]

        for f in files:
            if not isinstance(f, FMFile):
                raise FMFileError('File must be an FMFile instance')

            self._download(f, destination, callback)

    def _download(self, fmfile, destination, callback):
        """
        The actual downloader streaming content from Filemail.

        :param fmfile: :class:`FMFile` to download
        :param destination: `String` containing save path
        :param callback: pass instance of callback function that will receive a
            percentage of file transfered
        """

        filename = fmfile.get('filename')
        fullpath = os.path.join(destination, filename)
        filesize = fmfile.get('filesize')
        chunksize = 125000
        incr = 100.0 / (filesize / chunksize)
        count = 0

        url = fmfile.get('downloadurl')
        stream = self.session.send(method='get', url=url, stream=True)

        with open(fullpath, 'wb') as f:
            for chunk in stream.iter_content(chunksize):
                if not chunk:
                    break

                f.write(chunk)

                if callback is not None:
                    callback(int(incr * count))
                    count += 1

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

        :param callback: pass instance of callback function that will receive a
            percentage of file transfered
        :param auto_complete: `Boolean` settinng wheter or not to auto complete
            transfer after upload.

        If `auto_complete` is set to ``False`` you will have to call the
        :func:`complete` function
        at a later stage.
        """

        # TODO: Figure out a way to reimplement callback function and progress.
        tot = len(self.files)
        url = self.transfer_info['transferurl']

        for index, fmfile in enumerate(self.files):
            msg = 'Uploading: "{filename}" ({cur}/{tot})'
            logger.info(
                msg.format(
                    filename=fmfile['thefilename'],
                    cur=index + 1,
                    tot=tot)
                )

            with open(fmfile['filepath'], 'rb') as f:
                res = self.session.post(url, params=fmfile, data=f)

            res.text

            if res.status_code != 200:
                hellraiser(res)

        if auto_complete:
            return self.complete(keep_transfer_key=True)

        return res

    def complete(self, keep_transfer_key=False):
        """
        Completes the transfer and shoots off email(s) to recipients.

        :param keep_transfer_key: `Boolean` setting whether or not to keep the
            transfer key. This is needed for the :func:`update`
        """

        method, url = get_URL('complete')

        payload = {
            'apikey': self.session.cookies.get('apikey'),
            'transferid': self.transfer_info['transferid'],
            'transferkey': self.transfer_info['transferkey'],
            'keep_transfer_key': keep_transfer_key
            }

        res = getattr(self.session, method)(url, params=payload)

        if res.status_code != 200:
            hellraiser(res)

        self._complete = True

        return res

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

        method, url = getURL('update')

        payload = {
            'apikey': self.session.cookies.get('apikey'),
            'logintoken': self.config.get('logintoken'),
            'transferid': self.transferid,
            'message': kwargs.get('message'),
            'days': kwargs.get('days'),
            'downloads': kwargs.get('downloads'),
            'notify': kwargs.get('notify')
            }

        res = self.session.send(method=method, url=url, params=payload)

        if not res.ok:
            hellraiser(res.json())

        self.transfer_info.update(res.json())

    def delete(self):
        """
        Delete the current transfer.
        """

        method, url = getURL('delete')

        payload = {
            'apikey': self.session.cookies.get('apikey'),
            'transferid': self.transfer_info.get('transferid'),
            'logintoken': self.config.get('logintoken')
            }

        res = self.session.send(method=method, url=url, params=payload)

        if not res.ok:
            hellraiser(res.json())

    def zip(self):
        """
        Zip the current transfer on the server side.
        """

        method, url = getURL('zip')

        payload = {
            'apikey': self.session.cookies.get('apikey'),
            'transferid': self.transferid,
            'transferkey': self.transfer_info.get('transferkey')
            }

        res = self.session.send(method=method, url=url, params=payload)

        if not res.ok:
            hellraiser(res.json())

    def cancel(self):
        """
        Cancel the current transfer.
        """

        method, url = getURL('cancel')

        payload = {
            'apikey': self.session.cookies.get('apikey'),
            'transferid': self.transferid,
            'transferkey': self.transfer_info.get('transferkey')
            }

        res = self.session.send(method=method, url=url, params=payload)

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

        method, url = getURL('share')

        if 'to' in kwargs:
            to = kwargs.get('to')
            if isinstance(to, list):
                recipients = ','.join(to)
            else:
                recipients = to

        payload = {
            'apikey': self.session.cookies.get('apikey'),
            'logintoken': self.config.get('logintoken'),
            'transferid': self.transferid,
            'to': ','.join(recipients),
            'from': kwargs.get('from', self.config.get('username')),
            'message': kwargs.get('message')
            }

        res = self.session.send(method=method, url=url, params=payload)

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

        method, url = getURL('forward')

        payload = {
            'apikey': self.session.cookies.get('apikey'),
            'transferid': self.transferid,
            'transferkey': self.transfer_info.get('transferkey'),
            'to': to
            }

        res = self.session.send(method=method, url=url, params=payload)

        if not res.ok:
            hellraiser(res.json())

    def getFiles(self):
        """
        Get `List` of :class:`FMFile` objects for the current transfer.

        :returns: `List` of :class:`FMFile` objects

        """

        method, url = getURL('get')

        payload = {
            'apikey': self.session.cookies.get('apikey'),
            'transferid': self.transferid,
            'logintoken': self.config.get('logintoken')
            }

        res = self.session.send(method=method, url=url, params=payload)

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

        method, url = getURL('file_rename')

        payload = {
            'apikey': self.session.cookies.get('apikey'),
            'logintoken': self.config.get('logintoken'),
            'fileid': fmfile.get('fileid'),
            'filename': filename
            }

        res = self.session.send(method=method, url=url, params=payload)
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

        method, url = getURL('file_delete')

        payload = {
            'apikey': self.session.cookies.get('apikey'),
            'logintoken': self.config.get('logintoken'),
            'fileid': fmfile.get('fileid')
            }

        res = self.session.send(method=method, url=url, params=payload)
        if not res.ok:
            hellraiser(res.json())

        self._complete = True

    def _initialize(self):
        """Initialize transfer."""

        payload = {
            'apikey': self.session.cookies.get('apikey'),
            'source': self.session.cookies.get('source')
            }

        if self.fm_user.logged_in:
            payload['logintoken'] = self.session.cookies.get('logintoken')

        payload.update(self.transfer_info)

        method, url = get_URL('init')

        res = getattr(self.session, method)(url, params=payload)
        if res.status_code == 200:
            for key in ['transferid', 'transferkey', 'transferurl']:
                self.transfer_info[key] = res.json().get(key)

        else:
            hellraiser(res)

    def __repr__(self):
        return repr(self.transfer_info)