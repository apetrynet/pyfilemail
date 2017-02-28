import os
import datetime
from hashlib import md5
from uuid import uuid4
from mimetypes import guess_type
from zipfile import ZipFile

from clint.textui.progress import Bar as ProgressBar
from requests_toolbelt.multipart import encoder

import users
import pyfilemail as pm
from urls import get_URL
from functools import wraps
from pyfilemail import logger, login_required
from errors import hellraiser, FMBaseError, FMFileError


# Decorator to make sure we don't transfer complete packages twice
def not_completed(f):
    """Decorator function to check if user is loged in.

    :raises: :class:`FMBaseError` if not logged in
    """

    @wraps(f)
    def check_if_complete(cls, *args, **kwargs):
        if cls.is_complete:
            raise FMBaseError('Transfer already completed.')

        return f(cls, *args, **kwargs)

    return check_if_complete


class Transfer(object):
    """This is is the gateway to sending and recieving files through filemail.

    :param fm_user: username
    :param to: recipient(s)
    :param subject:
    :param message:
    :param notify: Notify when recipient(s) download files
    :param confirmation: Receive confirmation email when files are uploaded
    :param days: Number of days files are available for download
    :param downloads: Number of times files may be downloaded
    :param password: Protect download with given password
    :param checksum: Create checksum of added files (a bit slower process)
    :param zip_: Compress files in a zip file before sending
    :type zip_: bool
    :type checksum: bool
    :type password: str, unicode
    :type days: int
    :type confirmation: bool
    :type notify: bool
    :type message: str, unicode
    :type fm_user: :class:`pyfilemail.User`, str
    :type to: str, list
    :type subject: str, unicode
    """

    def __init__(self,
                 fm_user,
                 to=None,
                 subject=None,
                 message=None,
                 notify=False,
                 confirmation=False,
                 days=3,
                 downloads=0,
                 password=None,
                 checksum=True,
                 zip_=False,
                 _restore=False):

        if isinstance(fm_user, basestring):
            self.fm_user = users.User(fm_user)

        elif isinstance(fm_user, users.User):
            self.fm_user = fm_user

        else:
            raise FMBaseError('fm_user must be of type "string or User"')

        # Add transfer to user's transfer list
        self.fm_user.transfers.append(self)

        self._files = []

        self._complete = False
        self.checksum = checksum
        self.zip_ = zip_
        self.config = self.fm_user.config
        self.session = self.fm_user.session

        self.transfer_info = {
            'from': self.fm_user.username,
            'to': self._parse_recipients(to),
            'subject': subject,
            'message': message,
            'notify': notify,
            'confirmation': confirmation,
            'days': days,
            'downloads': downloads,
            'password': password
            }

        if not _restore:
            self._initialize()

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

    @property
    def logged_in(self):
        """If registered user is logged in or not.

        :rtype: bool
        """
        return self.session.cookies.get('logintoken') and True or False

    def _parse_recipients(self, to):
        """Make sure we have a "," separated list of recipients

        :param to: Recipient(s)
        :type to: (str,
                   list,
                   :class:`pyfilemail.Contact`,
                   :class:`pyfilemail.Group`
                   )
        :rtype: ``str``
        """

        if to is None:
            return None

        if isinstance(to, list):
            recipients = []

            for recipient in to:
                if isinstance(recipient, dict):
                    if 'contactgroupname' in recipient:
                        recipients.append(recipient['contactgroupname'])

                    else:
                        recipients.append(recipient.get('email'))

                else:
                    recipients.append(recipient)

        elif isinstance(to, basestring):
            if ',' in to:
                recipients = to.strip().split(',')

            else:
                recipients = [to]

        return ', '.join(recipients)

    def add_files(self, files):
        """Add files and/or folders to transfer.
        If :class:`Transfer.compress` attribute is set to ``True``, files
        will get packed into a zip file before sending.

        :param files: Files or folders to send
        :type files: str, list
        """

        if isinstance(files, basestring):
            files = [files]

        zip_file = None
        if self.zip_:
            zip_filename = self._get_zip_filename()
            zip_file = ZipFile(zip_filename, 'w')

        for filename in files:
            if os.path.isdir(filename):
                for dirname, subdirs, filelist in os.walk(filename):
                    if dirname:
                        if self.zip_:
                            zip_file.write(dirname)

                    for fname in filelist:
                        filepath = os.path.join(dirname, fname)
                        if self.zip_:
                            zip_file.write(filepath)

                        else:
                            fmfile = self.get_file_specs(filepath,
                                                         keep_folders=True)
                            if fmfile['totalsize'] > 0:
                                self._files.append(fmfile)

            else:
                if self.zip_:
                    zip_file.write(filename)

                else:
                    fmfile = self.get_file_specs(filename)
                    self._files.append(fmfile)

        if self.zip_:
            zip_file.close()
            filename = zip_filename
            fmfile = self.get_file_specs(filename)
            self._files.append(fmfile)

    @property
    def files(self):
        """:returns: List of files/folders added to transfer

        :rtype: ``list``
        """

        return self._files

    def get_file_specs(self, filepath, keep_folders=False):
        """Gather information on files needed for valid transfer.

        :param filepath: Path to file in question
        :param keep_folders: Whether or not to maintain folder structure
        :type keep_folders: bool
        :type filepath: str, unicode
        :rtype: ``dict``
        """

        path, filename = os.path.split(filepath)

        fileid = str(uuid4()).replace('-', '')

        if self.checksum:
            with open(filepath, 'rb') as f:
                md5hash = md5(f.read()).digest().encode('base64')[:-1]
        else:
            md5hash = None

        specs = {
            'transferid': self.transfer_id,
            'transferkey': self.transfer_info['transferkey'],
            'fileid': fileid,
            'filepath': filepath,
            'thefilename': keep_folders and filepath or filename,
            'totalsize': os.path.getsize(filepath),
            'md5': md5hash,
            'content-type': guess_type(filepath)[0]
            }

        return specs

    def get_files(self):
        """Get information on file in transfer from Filemail.

        :rtype: ``list`` of ``dict`` objects with info on files
        """

        method, url = get_URL('get')
        payload = {
            'apikey': self.session.cookies.get('apikey'),
            'logintoken': self.session.cookies.get('logintoken'),
            'transferid': self.transfer_id,
            }

        res = getattr(self.session, method)(url, params=payload)

        if res.status_code == 200:
            transfer_data = res.json()['transfer']
            files = transfer_data['files']

            for file_data in files:
                self._files.append(file_data)

            return self.files

        hellraiser(res)

    def _get_zip_filename(self):
        """Create a filename for zip file when :class:Transfer.compress is
        set to ``True``

        :rtype: str
        """

        date = datetime.datetime.now().strftime('%Y_%m_%d-%H%M%S')
        zip_file = 'filemail_transfer_{date}.zip'.format(date=date)

        return zip_file

    @not_completed
    def send(self, auto_complete=True, callback=None):
        """Begin uploading file(s) and sending email(s).
        If `auto_complete` is set to ``False`` you will have to call the
        :func:`Transfer.complete` function at a later stage.

        :param auto_complete: Whether or not to mark transfer as complete
         and send emails to recipient(s)
        :param callback: Callback function which will receive total file size
         and bytes read as arguments
        :type auto_complete: ``bool``
        :type callback: ``func``
        """

        tot = len(self.files)
        url = self.transfer_info['transferurl']

        for index, fmfile in enumerate(self.files):

            msg = 'Uploading: "{filename}" ({cur}/{tot})'
            logger.debug(
                msg.format(
                    filename=fmfile['thefilename'],
                    cur=index + 1,
                    tot=tot)
                )

            fields = {
                fmfile['thefilename']: (
                    'filename',
                    open(fmfile['filepath'], 'rb'),
                    fmfile['content-type']
                    )
                }

            def pg_callback(monitor):
                if pm.COMMANDLINE:
                    bar.show(monitor.bytes_read)

                elif callback is not None:
                    callback(fmfile['totalsize'], monitor.bytes_read)

            m_encoder = encoder.MultipartEncoder(fields=fields)
            monitor = encoder.MultipartEncoderMonitor(m_encoder, pg_callback)
            label = fmfile['thefilename'] + ': '

            if pm.COMMANDLINE:
                bar = ProgressBar(label=label,
                                  expected_size=fmfile['totalsize'])

            headers = {'Content-Type': m_encoder.content_type}

            res = self.session.post(url,
                                    params=fmfile,
                                    data=monitor,
                                    headers=headers)

            if res.status_code != 200:
                hellraiser(res)

        #logger.info('\r')
        if auto_complete:
            return self.complete()

        return res

    def complete(self):
        """Completes the transfer and shoots off email(s) to recipient(s)."""

        method, url = get_URL('complete')

        payload = {
            'apikey': self.session.cookies.get('apikey'),
            'transferid': self.transfer_id,
            'transferkey': self.transfer_info['transferkey']
            }

        res = getattr(self.session, method)(url, params=payload)

        if res.status_code != 200:
            hellraiser(res)

        self._complete = True

        return res

    @property
    def is_complete(self):
        """:rtype: ``bool`` ``True`` if transfer is complete"""

        if 'status' in self.transfer_info:
            self._complete = self.transfer_info['status'] == 'STATUS_COMPLETE'

        return self._complete

    @property
    def transfer_id(self):
        """
        Get the transfer id for the current Transfer.

        :rtype: ``unicode`` with transfer id
        """

        if 'transferid' in self.transfer_info:
            return self.transfer_info['transferid']

        return self.transfer_info['id']

    def forward(self, to):
        """Forward prior transfer to new recipient(s).

        :param to: new recipients to a previous transfer.
         Use ``list`` or  comma seperatde ``str`` or ``unicode`` list
        :type to: ``list`` or ``str`` or ``unicode``
        :rtype: ``bool``

        """

        method, url = get_URL('forward')

        payload = {
            'apikey': self.session.cookies.get('apikey'),
            'transferid': self.transfer_id,
            'transferkey': self.transfer_info.get('transferkey'),
            'to': self._parse_recipients(to)
            }

        res = getattr(self.session, method)(url, params=payload)

        if res.status_code == 200:
            return True

        hellraiser(res)

    @login_required
    def share(self, to, sender=None, message=None):
        """Share transfer with new message to new people.

        :param to: receiver(s)
        :param sender: Alternate email address as sender
        :param message: Meggase to new recipients
        :type to: ``list`` or ``str`` or ``unicode``
        :type sender: ``str`` or ``unicode``
        :type message: ``str`` or ``unicode``
        :rtyep: ``bool``
        """

        method, url = get_URL('share')

        payload = {
            'apikey': self.session.cookies.get('apikey'),
            'logintoken': self.session.cookies.get('logintoken'),
            'transferid': self.transfer_id,
            'to': self._parse_recipients(to),
            'from': sender or self.fm_user.username,
            'message': message or ''
            }

        res = getattr(self.session, method)(url, params=payload)

        if res.status_code == 200:
            return True

        hellraiser(res)

    def cancel(self):
        """Cancel the current transfer.

        :rtype: ``bool``
        """

        method, url = get_URL('cancel')

        payload = {
            'apikey': self.config.get('apikey'),
            'transferid': self.transfer_id,
            'transferkey': self.transfer_info.get('transferkey')
            }

        res = getattr(self.session, method)(url, params=payload)

        if res.status_code == 200:
            self._complete = True
            return True

        hellraiser(res)

    @login_required
    def delete(self):
        """Delete the current transfer.

        :rtype: ``bool``
        """

        method, url = get_URL('delete')

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.session.cookies.get('logintoken'),
            'transferid': self.transfer_id
            }

        res = getattr(self.session, method)(url, params=payload)

        if res.status_code == 200:
            return True

        hellraiser(res)

    @login_required
    def rename_file(self, fmfile, newname):
        """Rename file in transfer.

        :param fmfile: file data from filemail containing fileid
        :param newname: new file name
        :type fmfile: ``dict``
        :type newname: ``str`` or ``unicode``
        :rtype: ``bool``
        """

        if not isinstance(fmfile, dict):
            raise FMBaseError('fmfile must be a <dict>')

        method, url = get_URL('file_rename')

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.session.cookies.get('logintoken'),
            'fileid': fmfile.get('fileid'),
            'filename': newname
            }

        res = getattr(self.session, method)(url, params=payload)
        if res.status_code == 200:
            self._complete = True
            return True

        hellraiser(res)

    @login_required
    def delete_file(self, fmfile):
        """Delete file from transfer.

        :param fmfile: file data from filemail containing fileid
        :type fmfile: ``dict``
        :rtype: ``bool``
        """

        if not isinstance(fmfile, dict):
            raise FMFileError('fmfile must be a <dict>')

        method, url = get_URL('file_delete')

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.session.cookies.get('logintoken'),
            'fileid': fmfile.get('fileid')
            }

        res = getattr(self.session, method)(url, params=payload)

        if res.status_code == 200:
            self._complete = True
            return True

        hellraiser(res)

    @login_required
    def update(self,
               message=None,
               subject=None,
               days=None,
               downloads=None,
               notify=None):
        """Update properties for a transfer.

        :param message: updated message to recipient(s)
        :param subject: updated subject for trasfer
        :param days: updated amount of days transfer is available
        :param downloads: update amount of downloads allowed for transfer
        :param notify: update whether to notifiy on downloads or not
        :type message: ``str`` or ``unicode``
        :type subject: ``str`` or ``unicode``
        :type days: ``int``
        :type downloads: ``int``
        :type notify: ``bool``
        :rtype: ``bool``
        """

        method, url = get_URL('update')

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.session.cookies.get('logintoken'),
            'transferid': self.transfer_id,
            }

        data = {
            'message': message or self.transfer_info.get('message'),
            'message': subject or self.transfer_info.get('subject'),
            'days': days or self.transfer_info.get('days'),
            'downloads': downloads or self.transfer_info.get('downloads'),
            'notify': notify or self.transfer_info.get('notify')
            }

        payload.update(data)

        res = getattr(self.session, method)(url, params=payload)

        if res.status_code:
            self.transfer_info.update(data)
            return True

        hellraiser(res)

    def download(self,
                 files=None,
                 destination=None,
                 overwrite=False,
                 callback=None):

        """Download file or files.

        :param files: file or files to download
        :param destination: destination path (defaults to users home directory)
        :param overwrite: replace existing files?
        :param callback: callback function that will receive total file size
         and written bytes as arguments
        :type files: ``list`` of ``dict`` with file data from filemail
        :type destination: ``str`` or ``unicode``
        :type overwrite: ``bool``
        :type callback: ``func``
        """

        if files is None:
            files = self.files

        elif not isinstance(files, list):
            files = [files]

        if destination is None:
            destination = os.path.expanduser('~')

        for f in files:
            if not isinstance(f, dict):
                raise FMBaseError('File must be a <dict> with file data')

            self._download(f, destination, overwrite, callback)

    def _download(self, fmfile, destination, overwrite, callback):
        """The actual downloader streaming content from Filemail.

        :param fmfile: to download
        :param destination: destination path
        :param overwrite: replace existing files?
        :param callback: callback function that will receive total file size
         and written bytes as arguments
        :type fmfile: ``dict``
        :type destination: ``str`` or ``unicode``
        :type overwrite: ``bool``
        :type callback: ``func``
        """

        fullpath = os.path.join(destination, fmfile.get('filename'))
        path, filename = os.path.split(fullpath)

        if os.path.exists(fullpath):
            msg = 'Skipping existing file: {filename}'
            logger.info(msg.format(filename=filename))
            return

        filesize = fmfile.get('filesize')

        if not os.path.exists(path):
            os.makedirs(path)

        url = fmfile.get('downloadurl')
        stream = self.session.get(url, stream=True)

        def pg_callback(bytes_written):
            if pm.COMMANDLINE:
                bar.show(bytes_written)

            elif callback is not None:
                callback(filesize, bytes_written)

        if pm.COMMANDLINE:
            label = fmfile['filename'] + ': '
            bar = ProgressBar(label=label, expected_size=filesize)

        bytes_written = 0
        with open(fullpath, 'wb') as f:
            for chunk in stream.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    break

                f.write(chunk)
                bytes_written += len(chunk)

                # Callback
                pg_callback(bytes_written)

    @login_required
    def compress(self):
        """Compress files on the server side after transfer complete
         and make zip available for download.

        :rtype: ``bool``
        """

        method, url = get_URL('compress')

        payload = {
            'apikey': self.config.get('apikey'),
            'logintoken': self.session.cookies.get('logintoken'),
            'transferid': self.transfer_id
            }

        res = getattr(self.session, method)(url, params=payload)

        if res.status_code == 200:
            return True

        hellraiser(res)

    def __getitem__(self, key):
        return self.transfer_info[key]

    def __setitem__(self, key, value):
        self.transfer_info[key] = value

    def __repr__(self):
        return repr(self.transfer_info)
