NOTE!
=====
This is still work in progress and parts of the API might chnage as I test it further.

pyfilemail
==========

Pyfilemail is a command line tool and API for sending and recieving files with `Filemail <https://www.filemail.com>`_ based on filemail's `official API <https://www.filemail.com/apidoc/ApiDocumentation.aspx>`_
and `requests <https://github.com/kennethreitz/requests>`_

You should register and get an `API KEY <http://www.filemail.com/apidoc/ApiKey.aspx>`_ to unlock all features and be able to add/delete/update your transfers.
You'll be able to send files without registering, but remember to use the "--anonymous" option in the tool.

As it is now the API is a thin wrapper around filemail's REST API. Appart from :class:`pyfilemail.User` and :class:`pyfilemail.Transfer` classes, all return objects from filemail are kept as ``dict`` based on the json response.

I've tried to keep this api as simple as possible and rely on filemail's own validation of data and error codes to keep you all in check :) The reason for this is that I don't work at filemail and have no insight in what validation they have for the data passed.
It also saves me a lot of head ache writing rock solid validation code and I think this is a more flexible way of doing it. Please correct me if I'm wrong here.

So far this has been developed and tested on Ubuntu. I'll try to get my hands on a Windows and OSX machine and addapt the code to make sure it works there as well.

Any feedback is more than welcome and please report bugs through `github <https://github.com/apetrynet/pyfilemail/issues>`_

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

    # Download received transfers for the past 7 days
    transfers = user.get_received(age=7)
    for transfer in transfers:
        transfer.download(destination=/home/myname/Downloads)

    # Logout
    user.logout()

