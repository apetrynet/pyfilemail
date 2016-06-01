#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import argparse
import getpass
import logging

import keyring
from keyring.errors import PasswordDeleteError

KEYRING = True
k = keyring.get_keyring()
if isinstance(k, keyring.backends.fail.Keyring):
    KEYRING = False

from pyfilemail import logger, streamhandler
from users import User
from transfer import Transfer

unicodize = lambda s: unicode(s, 'utf-8')


def parse_args():
    description = 'Command line Filemail transfer through Python'
    prog = 'python -m pyfilemail'

    parser = argparse.ArgumentParser(prog=prog, description=description)
    parser.add_argument('-un',
                        '--unregistered',
                        dest='unregistered',
                        action='store_true',
                        default=False,
                        help='Send files without a registered Filemail account')

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
                        type=unicodize,
                        default='Sent with \
https://github.com/apetrynet/pyfilemail',
                        help='Message to the recipient(s) of the transfer')

    parser.add_argument('--notify',
                        dest='notify',
                        action='store_true',
                        default=False,
                        help='Notify when recipients download your files?')

    parser.add_argument('--subject',
                        dest='subject',
                        action='store',
                        type=unicodize,
                        default='',
                        help='Subject of email sent with transfer')

    parser.add_argument('--to',
                        dest='to',
                        required=True,
                        action='store',
                        nargs='+',
                        type=unicodize,
                        default=None,
                        metavar='recipient@receiver.com',
                        help='Recipient(s) of the transfer (email addresses)')

    parser.add_argument('--password',
                        dest='password',
                        action='store',
                        type=unicodize,
                        default='',
                        help='Protect transfer with the supplied password')

    parser.add_argument('--username',
                        dest='username',
                        action='store',
                        required=True,
                        type=unicodize,
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

    if args.console:
        streamhandler.setLevel(logging.INFO)
        logger.info('Logging to console enabled.')

    if args.delete_password and KEYRING:
        try:
            keyring.delete_password('pyfilemail', args.username)
            msg = 'Password for {user} successfully deleted.'
            sys.exit(msg.format(user=args.username))

        except PasswordDeleteError:
            pass

    return args


if __name__ == '__main__':
    args = parse_args()

    pwd = None

    if not args.unregistered:
        if KEYRING:
            pwd = keyring.get_password('pyfilemail', args.username)

        if pwd is None:
            pwd = getpass.getpass('Please enter Filemail password: ')
            if args.store_password and KEYRING:
                keyring.set_password('pyfilemail', args.username, pwd)

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
        zip_=args.compress
        )

    transfer.add_files(args.payload)

    res = transfer.send()

    if res.status_code == 200:
        msg = 'Transfer complete!'
        logger.info(msg)
