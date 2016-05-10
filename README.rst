NOTE!
=====
I'm in the middle of a major rewrite so the documentation and some of the methods are out of date. You should be able to send files with the command line tool. Thing will change and the rest of the API will get refactored.

==========
pyfilemail
==========

Python command line tool and API for sending and recieving files with `<www.filemail.com>`_

pyfilemail uses filemail's `official API <http://www.filemail.com/apidoc/ApiDocumentation.aspx>`_
and `requests <https://github.com/kennethreitz/requests>`_

Example Usages
==============

You should register and get an `API KEY <http://www.filemail.com/apidoc/ApiKey.aspx>`_
to unlock all features and be able to add/delete/update your transfers. 
You'll be able to send files without registering, but remember to use the "-a | --anonymous" option in the tool.


Command line
************

..  code-block:: bash

    python -m pyfilemail \
    --subject "Amazing document!" \
    --message "Have you seen this amazing document?" \
    --username myemail@somedomain.com \
    --to lucky.b@receiver.com \
    --payload /path/to/file.ext /path/to/folder/

Python (outdated)
*****************

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

