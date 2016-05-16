NOTE!
=====
I'm in the middle of a major rewrite so the documentation and some of the methods are out of date.
You should be able to send files with the command line tool. Thing will change and the rest of the API will get refactored.


pyfilemail
==========

Pyfilemail is a command line tool and API for sending and recieving files with `Filemail <https://www.filemail.com>`_ based on filemail's `official API <https://www.filemail.com/apidoc/ApiDocumentation.aspx>`_
and `requests <https://github.com/kennethreitz/requests>`_

You should register and get an `API KEY <http://www.filemail.com/apidoc/ApiKey.aspx>`_ to unlock all features and be able to add/delete/update your transfers.
You'll be able to send files without registering, but remember to use the "--anonymous" option in the tool.


Command line example
********************

..  code-block:: bash

    python -m pyfilemail \
    --subject "Amazing document!" \
    --message "Have you seen this amazing document?" \
    --username myemail@somedomain.com \
    --to lucky.b@receiver.com \
    --payload /path/to/file.ext /path/to/folder/


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

Python API examples
*******************

..  code-block:: python

    import pyfilemail

    # Login to a Filemail account
    user = pyfilemail.User(username='user@mailprovider.com',
                           password='YourSecretPassword2014')

    # List all prior transfers
    transfers = user.get_sent(expired=True)

    # Setup a transfer
    transfer = pyfilemail.Transfer(user,
                                   to='lucky@recipient.com',
                                   subject='My BIG file no email can handle',
                                   message='You will not belive the speed of this download!',
                                   notify=True,
                                   confirmation=True,
                                   days=7,
                                   password='JuSt2BeSaf£')

    # Add a single file to transfer queue
    transfer.add_files('/path/to/my/BIG_file.ext')

    # Add multiple files
    list_of_files = ['/path/to/my/BIG_file_1.ext',
                     '/path/to/my/BIG_file_2.ext',
                     '/path/to/my/BIG_file_3.ext']

    transfer.add_files(list_of_files)

    # Send files to recipient(s)
    transfer.send(auto_complete=True)

    # Get contacts
    user.get_contacts()

    # Get one single contact
    contact = user.get_contact('contact@email.address.com')

    # Update that contact
    contact['name'] = 'Mr. Orange'
    user.update_contact(contact)

    # Delete contact
    unfriendly = user.get_contact('contact@email.address.com')
    user.delete_contact(unfriendly)

    # Logout
    user.logout()

