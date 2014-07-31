Welcome to filemail's documentation!
====================================

(Unofficial) Pyhton API for sending and recieving files with
`<www.filemail.com>`_ written by: Daniel Flehner Heen.

filemail Pyhton API is built around filemail's
`official API <http://www.filemail.com/apidoc/ApiDocumentation.aspx>`_
using `requests <https://github.com/kennethreitz/requests>`_ by Kenneth Reitz.


Contents
========

..  toctree::
    :maxdepth: 2

    license
    api
    configfile


Example Usage
=============

You will need a valid `API-key <http://www.filemail.com/apidoc/ApiKey.aspx>`_
from filemail and a registered user to be able to send files.

..  code-block:: python

    import filemail

    # Login to a Filemail account
    user = filemail.login(username='user@mailprovider.com',
                          apikey='YOUR-APIKEY-FROM-FILEMAIL-GOES-HERE',
                          password='YourSecretPassword2014')

    # Setup a transfer
    transfer = filemail.Transfer(user,
                                 to='lucky@recipient.com',
                                 subject='My BIG file no email can handle',
                                 message='You will not belive the speed of this download!',
                                 notify=True,
                                 confirmation=True,
                                 days=7,
                                 password='JuSt2BeSaf£')

    # Add a single file to queue
    transfer.addFile('/path/to/my/BIG_file.ext')

    # Add multiple files
    list_of_files = ['/path/to/my/BIG_file_1.ext',
                     '/path/to/my/BIG_file_2.ext',
                     '/path/to/my/BIG_file_3.ext']

    transfer.addFiles(list_of_files)

    # Send files to recipient(s)
    transfer.send(callback=myCallbackFunction, auto_complete=True)

    # Logout
    user.logout()


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

