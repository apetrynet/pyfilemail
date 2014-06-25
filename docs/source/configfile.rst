..  _example-configfile:

Configfile Example
==================

Place a config file named filemail.cfg in one of the following locations:

* ``${HOME}/filemail.cfg``
* in the folder above filemail package
* or in any location set in evironment variable called ``FILEMAIL_CONFIG_FILE``

..  code-block:: none

    [username@emailprovider.com]

    username = username@emailprovider.com
    apikey = YOUR-API-KEY-FROM-FILEMAIL-SUPPORT
    password = secretpassword
    defaultdownloads = 30
    logintoken = fdc8893e983c98a02b938c9289298c92
    name = Firstname Lastname
    defaultnotify = True
    country = NO
    defaultconfirmation = True
    defaultdays = 7
    source = web
    newsletter = True
    defaultsubject = Sending files through filemail python API
    signature = Have a nice day!
    email = username@emailprovider.com

