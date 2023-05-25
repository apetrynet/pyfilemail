# This Project is Discontinued

Unfortunately this project is discontinued until further notice. 

Please consider using Filemail's [CLI](https://www.filemail.com/apidoc/FilemailLibs.aspx) for your scripting needs. You should be able to wrap the CLI in a subprocess.

Welcome to pyfilemail's documentation!
=======================================

Pyfilemail is a command line tool and API for sending and recieving files with [Filemail](https://www.filemail.com) based on [requests](https://github.com/kennethreitz/requests) and filemail's [API](https://www.filemail.com/apidoc/ApiDocumentation.aspx).

To avoid nagging about API KEY you should register and get one [here](http://www.filemail.com/apidoc/ApiKey.aspx). If you register for 
a paid plan you unlock all features and will be able to add/delete/update your  ransfers/contacts/group/company settings.
Without registering you'll still be able to send files as a free plan user but remember to use the `--free` argument in the command line tool.

For more info on the different plans please go to [Filemail](https://www.filemail.com)

I've tried to keep this api as simple as possible and rely on filemail's own validation of data to keep you all in check :) The reason for this is that I don't work at filemail and have no insight in what validation they have for the data passed. It also saves me a lot of head ache writing rock solid validation code and I think this is a more flexible way of doing it if the Filemail team decides to change the API in any way.

Appart from `pyfilemail.User` and `pyfilemail.Transfer` classes, all return objects from filemail are `dict` objects based on json responses.

So far this has been developed and tested on Ubuntu 16.04. I'll try to get my hands on a Windows and OSX machine and addapt the code to make sure it works there as well.

API documentation is available at [readthedocs](http://pyfilemail.readthedocs.io/en/latest/)

Any feedback is more than welcome and please report bugs through [github](https://github.com/apetrynet/pyfilemail/issues)

Installation
============

```
pip install pyfilemail
```

Disclaimer
==========

I use this software myself and have not yet experienced broken files, but I take no responsibility for the files sent or received using `pyfilemail` whether it comes to content or state of files passing through. Pyfilemail is still work in progress and parts of the API might change as I develop and test it further.

Command line example
====================

```
pyfilemail \
--from myemail@somedomain.com \
--to lucky.b@receiver.com \
--free \
--subject "Amazing document!" \
--message "Have you seen how amazingly big this document is?" \
--payload /path/to/file.ext /path/to/folder/
```

Add API KEY
===========

You can add the API KEY to the local config file with the `--add-api-key` argumet.

```
pyfilemail --add-api-key YOUR-API-KEY-FROM-FILEMAIL
```

netrc
=====

You may use a .netrc file to store login information. Make sure you restrict access to only allow your own user to read it.

```
#$HOME/.netrc example:
machine yourfilemailuser@email.com
        login yourfilemailuser@email.com
        password topsecretpassword
```

Command line help
=================

```
usage: pyfilemail [-h] [--version] [--add-api-key ADD_API_KEY] [--free] [-nc]
              [--compress] [--confirm] [--quiet] [--days 3]
              [--downloads 0] [--message MESSAGE] [--notify]
              [--subject SUBJECT]
              [--to recipient@receiver.com [recipient@receiver.com ...]]
              [--password PASSWORD] [--from USERNAME] [--store-password]
              [--delete-password] [--payload PAYLOAD [PAYLOAD ...]]

Command line Filemail transfer through Python

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --add-api-key ADD_API_KEY
                        Add API KEY from Filemail to local config file
  --free                Send files without a registered Filemail account
  -nc, --no-checksum    Skip calculating checksum on added files
  --compress            Compress (ZIP) data before sending?
  --confirm             Email confirmation after sending the files?
  --quiet               Log only warnings to console
  --days 3              Number of days the file(s) are available for download
  --downloads 0         Number of times the file(s) may be downloaded.
                        0=unlimited
  --message MESSAGE     Message to the recipient(s) of the transfer
  --notify              Notify when recipients download your files?
  --subject SUBJECT     Subject of email sent with transfer
  --to recipient@receiver.com [recipient@receiver.com ...]
                        Recipient(s) of the transfer (email addresses)
  --password PASSWORD   Protect transfer with the supplied password
  --from USERNAME       Your email address
  --store-password      Store user password in keychain if available
  --delete-password     Delete password stored in keychain
  --payload PAYLOAD [PAYLOAD ...]
                        File(s) and/or folder(s) to transfer
```

Python API examples
===================

```
import pyfilemail

# Setup a transfer

# Initialize Filemail with as free (as in free beer) user
user = pyfilemail.User(username='user@mailprovider.com')

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

# Login to a registered Filemail account
user = pyfilemail.User(username='user@mailprovider.com',
                       password='YourSecretPassword2014')

# List all prior transfers
transfers = user.get_sent(expired=True)

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
    transfer.download(destination='/home/myname/Downloads')

# Logout
user.logout()
```
