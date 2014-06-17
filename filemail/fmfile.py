import os

from hashlib import md5
from uuid import uuid4
from mimetypes import guess_type


class FMFile():

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

    def addFile(self, filename):
        if not os.path.isfile(filename):
            raise Exception('No such file: {}'.format(filename))

        self.path, self.filename = os.path.split(filename)

        self.updateFileInfo(self.getFileSpecs())

    def download(self, path):
        pass

    def set(self, key, value):
        self._file_info[key] = value

    def get(self, key):
        if key in self._file_info:
            return self._file_info[key]

        return None

    def updateFileInfo(self, data):
        if not isinstance(data, dict):
            raise Exception('A dict must be passed')

        for key, value in data.items():
            self.set(key, value)

    def fileInfo(self):
        return self._file_info

    def getFileSpecs(self):
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