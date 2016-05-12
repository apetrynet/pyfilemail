.. pyfilemail documentation master file, created by
   sphinx-quickstart on Wed May 11 00:07:47 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to pyfilemail's documentation!
======================================

Python command line tool and API for sending and recieving files with `Filemail <https://www.filemail.com>`_

pyfilemail uses filemail's `official API <https://www.filemail.com/apidoc/ApiDocumentation.aspx>`_
and `requests <https://github.com/kennethreitz/requests>`_

Example Usages
--------------

You should register and get an `API KEY <http://www.filemail.com/apidoc/ApiKey.aspx>`_
to unlock all features and be able to add/delete/update your transfers. 
You'll be able to send files without registering, but remember to use the "-a | --anonymous" option in the tool.

Command line help
*****************

..  code-block:: bash

    python -m pyfilemail -h
    usage: python -m pyfilemail [-h] [-a] [-nc] [--compress] [--confirm]
                                [--console] [--days DAYS] [--downloads DOWNLOADS]
                                [--message MESSAGE] [--notify] [--subject SUBJECT]
                                --to recipient@receiver.com
                                [recipient@receiver.com ...] [--password PASSWORD]
                                --username USERNAME [--store-password]
                                [--delete-password] --payload PAYLOAD
                                [PAYLOAD ...]

    Command line Filemail transfer through Python
    
    optional arguments:
      -h, --help            show this help message and exit
      -a, --anonymous       No active filemail account
      -nc, --no-checksum    Don't calculate checksum on added files
      --compress            Compress (ZIP) data before sending?
      --confirm             Email confirmation after sending the files?
      --console             Logs to console
      --days DAYS           Number of days the file(s) can be downloaded
      --downloads DOWNLOADS
                            Number of times the file(s) can be downloaded
      --message MESSAGE     Message to the recipient(s) of the transfer
      --notify              Notify when recipients download your files?
      --subject SUBJECT     Subject of email sent with transfer
      --to recipient@receiver.com [recipient@receiver.com ...]
                            Recipient(s) of the transfer (email addresses)
      --password PASSWORD   Protect transfer with the supplied password
      --username USERNAME   Your email address
      --store-password      Store user password in keychain
      --delete-password     Delete password stored in keychain
      --payload PAYLOAD [PAYLOAD ...]
                            File(s) and/or folder(s) to transfer


Command line example
********************

..  code-block:: bash

    python -m pyfilemail \
    --subject "Amazing document!" \
    --message "Have you seen this amazing document?" \
    --username myemail@somedomain.com \
    --to lucky.b@receiver.com \
    --payload /path/to/file.ext /path/to/folder/

Python api example (outdated)
*****************************

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

API
===

..  automodule:: pyfilemail
    :members:
    :undoc-members:
    
..  autoclass:: User
    :members:
    :undoc-members:
    
..  autoclass:: Transfer
    :members:
    :undoc-members:
    
Contents:

.. toctree::
   :maxdepth: 2



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

