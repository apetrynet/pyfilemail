import os

from hashlib import md5
from uuid import uuid4
from mimetypes import guess_type


class FMFile():
    """
    FMFile contains information on a file for upload and download. It can also
    represent file information on files from older transfers.

    :param fullpath: (optional) `String` to file
    :param data: (optional) `Dictionary` containig information and specs
    """

    def __init__(self, fullpath=None, data=None):
        self._file_info = {}
        self.fullpath = fullpath
        self.path = None
        self.filename = None
        self.config = None

        if self.fullpath is not None:
            self.addFile(self.fullpath)

        if data is not None:
            self.updateFileInfo(data)

    def addFile(self, fullpath):
        """
        Registers file with class and updates information.

        :param fullpath: `String` with full path to file
        """

        if not os.path.isfile(fullpath):
            raise Exception('No such file: {}'.format(fullpath))

        self.path, self.filename = os.path.split(fullpath)

        self.updateFileInfo(self.getFileSpecs())

    def download(self, path):
        raise NotImplemented()

    def set(self, key, value):
        """
        Set a value for given key in file information.

        :param key: `String` with keyname
        :param value: `String` or `Int` for key name
        """

        self._file_info[key] = value

    def get(self, key):
        """
        Get value for given key.

        :param key: `String` with valid key name
        :returns: `String` or `Int` for key. `None` if empty or no key by that
            name in file information
        """

        if key in self._file_info:
            return self._file_info[key]

        return None

    def updateFileInfo(self, data):
        """
        Bulk update of file information.

        :param data: `Dictionary` containing information
        """

        if not isinstance(data, dict):
            raise Exception('A dict must be passed')

        for key, value in data.items():
            self.set(key, value)

    def fileInfo(self):
        """:returns: `Dictionary` with current information on a file"""

        return self._file_info

    def getFileSpecs(self):
        """
        Collects all file specs needed for transfer of file to filemail.com.

        :returns: `Dictionary` with file specs
        """

        fileid = str(uuid4()).replace('-', '')
        md5hash = md5(open(self.fullpath, 'rb').read()).digest()
        compressed = self.filename[-3:] in ['zip', 'rar', 'tar', '.gz', '.7z']

        specs = {
            'fileid': fileid,
            'filename': self.filename,
            'thefilename': self.filename,
            'totalsize': os.path.getsize(self.fullpath),
            'md5': md5hash.encode('base64')[:-1],
            'compressed': compressed,
            'content-type': guess_type(self.fullpath)[0],
            'chunkpos': 0
            }

        return specs

    def __repr__(self):
        return repr(self.fileInfo())