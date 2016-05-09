#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import argparse
import getpass

import keyring
from keyring.errors import PasswordDeleteError

KEYRING = True
k = keyring.get_keyring()
if isinstance(k, keyring.backends.fail.Keyring):
    KEYRING = False

from users import User
from transfer import Transfer

unishizzle = lambda s: unicode(s, 'utf-8')


def parse_args():
    description = 'Command line filemail transfer through Python'

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-a',
                        '--anonymous',
                        dest='anonymous',
                        action='store_true',
                        default=False,
                        help='No active filemail account')

    parser.add_argument('-nc',
                        '--no-checksum',
                        dest='checksum',
                        action='store_false',
                        default=True,
                        help="Don't calculate checksum on added files")

    parser.add_argument('--compress',
                        dest='compress',
                        action='store_true',
                        default=False,
                        help='Compress (ZIP) data before sending?')

    parser.add_argument('--confirm',
                        dest='confirm',
                        action='store_true',
                        default=False,
                        help='Email confirmation after sending the files?')

    parser.add_argument('--console',
                        dest='console',
                        action='store_true',
                        default=False,
                        help='Logs to console')

    parser.add_argument('--days',
                        dest='days',
                        action='store',
                        type=int,
                        default=3,
                        help='Number of days the file(s) can be downloaded')

    parser.add_argument('--downloads',
                        dest='downloads',
                        action='store',
                        type=int,
                        default=0,
                        help='Number of times the file(s) can be downloaded')

    parser.add_argument('--message',
                        dest='message',
                        action='store',
                        type=unishizzle,
                        default='Files sent with filemail.py',
                        help='Message to the recipient(s) of the transfer')

    parser.add_argument('--notify',
                        dest='notify',
                        action='store_true',
                        default=False,
                        help='Notify when recipients download your files?')

    parser.add_argument('--subject',
                        dest='subject',
                        action='store',
                        type=unishizzle,
                        default='',
                        help='Subject of email sent with transfer')

    parser.add_argument('--to',
                        dest='to',
                        required=True,
                        action='store',
                        nargs='+',
                        type=unishizzle,
                        default=None,
                        metavar='recipient@receiver.com',
                        help='Recipient(s) of the transfer (email addresses)')

    parser.add_argument('--password',
                        dest='password',
                        action='store',
                        type=unishizzle,
                        default='',
                        help='Protect transfer with the supplied password')

    parser.add_argument('--username',
                        dest='username',
                        action='store',
                        required=True,
                        type=unishizzle,
                        default=None,
                        help='Your email address')

    parser.add_argument('--store-password',
                        dest='store_password',
                        action='store_true',
                        default=False,
                        help='Store user password in keychain')

    parser.add_argument('--delete-password',
                        dest='delete_password',
                        action='store_true',
                        default=False,
                        help='Delete password stored in keychain')

    parser.add_argument('--payload',
                        action='store',
                        dest='payload',
                        default=None,
                        required=True,
                        nargs='+',
                        help='File(s) and/or folder(s) to transfer')

    args = parser.parse_args()

    if args.delete_password and KEYRING:
        try:
            keyring.delete_password('filemail', args.username)
            msg = 'Password for {user} successfully deleted.'
            sys.exit(msg.format(user=args.username))

        except PasswordDeleteError:
            pass

    return args


if __name__ == '__main__':
    args = parse_args()

    pwd = None

    if not args.anonymous:
        if KEYRING:
            pwd = keyring.get_password('filemail', args.username)

        if pwd is None:
            pwd = getpass.getpass('Please enter Filemail password: ')
            if args.store_password and KEYRING:
                keyring.set_password('filemail', args.username, pwd)

    fm_user = User(args.username, password=pwd)

    transfer = Transfer(
        fm_user,
        to=args.to,
        subject=args.subject,
        message=args.message,
        notify=args.notify,
        confirmation=args.confirm,
        days=args.days,
        password=args.password,
        checksum=args.checksum,
        compress=args.compress
        )

    transfer.add_files(args.payload)

    #print 'Sending files...'
    res = transfer.send()

    if res.status_code == 200:
        msg = 'Files sent successfully!'
        print msg
