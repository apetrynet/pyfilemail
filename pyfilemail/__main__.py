#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import argparse
import getpass
import logging
#from netrc import netrc, NetrcParseError

import keyring
from keyring.errors import PasswordDeleteError

# Check for keyring
KEYRING = True
k = keyring.get_keyring()
if isinstance(k, keyring.backends.fail.Keyring):
    KEYRING = False

import pyfilemail as pm
from pyfilemail import (
    logger,
    streamhandler,
    load_config,
    save_config,
    get_configfile,
    __version__
    )

from users import User
from transfer import Transfer

unicodize = lambda s: unicode(s, 'utf-8')


def parse_args():
    description = 'Command line Filemail transfer through Python'
    prog = 'pyfilemail'

    parser = argparse.ArgumentParser(prog=prog, description=description)
    parser.add_argument('--version',
                        action='version',
                        version='%(prog)s' + __version__)

    parser.add_argument('--add-api-key',
                        dest='add_api_key',
                        action='store',
                        type=unicodize,
                        default=None,
                        help='Add API KEY from Filemail to local config file')
    parser.add_argument('--free',
                        dest='free',
                        action='store_true',
                        default=False,
                        help='Send files without a registered Filemail account')

    parser.add_argument('-nc',
                        '--no-checksum',
                        dest='checksum',
                        action='store_false',
                        default=True,
                        help="Skip calculating checksum on added files")

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

    parser.add_argument('--quiet',
                        dest='quiet',
                        action='store_true',
                        default=False,
                        help='Log only warnings to console')

    parser.add_argument('--days',
                        dest='days',
                        action='store',
                        type=int,
                        default=3,
                        metavar=3,
                        help='Number of days the file(s) are available for \
download')

    parser.add_argument('--downloads',
                        dest='downloads',
                        action='store',
                        type=int,
                        default=0,
                        metavar=0,
                        help='Number of times the file(s) may be downloaded. \
0=unlimited')

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

    parser.add_argument('--from',
                        dest='username',
                        action='store',
                        type=unicodize,
                        default=None,
                        help='Your email address')

    parser.add_argument('--store-password',
                        dest='store_password',
                        action='store_true',
                        default=False,
                        help='Store user password in keychain if available')

    parser.add_argument('--delete-password',
                        dest='delete_password',
                        action='store_true',
                        default=False,
                        help='Delete password stored in keychain')

    parser.add_argument('--payload',
                        action='store',
                        dest='payload',
                        default=None,
                        nargs='+',
                        help='File(s) and/or folder(s) to transfer')

    # Display help if no arguments are provided
    if len(sys.argv) == 1:
        sys.exit(parser.print_help())

    args = parser.parse_args()

    # Add API KEY if provided
    if args.add_api_key is not None:
        config = load_config()
        config['apikey'] = args.add_api_key
        save_config(config)

        msg = 'API KEY: "{apikey}" added to {conf}'
        logger.info(msg.format(apikey=args.add_api_key, conf=get_configfile()))
        sys.exit()

    # Check if user wants to delete password stored in keychain
    if args.delete_password and KEYRING:
        try:
            keyring.delete_password('pyfilemail', args.username)
            msg = 'Password for {user} successfully deleted.'
            sys.exit(msg.format(user=args.username))

        except PasswordDeleteError:
            pass

    # Check for username
    if args.username is None:
        msg = 'Please provide your email address to the --from argument'
        logger.error(msg)
        sys.exit(1)

    # Check for recipient(s)
    if args.to is None:
        msg = 'Please provide recipient(s) to the --to argument'
        logger.error(msg)
        sys.exit(1)

    # Check for files and folders to send
    if args.payload is None:
        msg = 'Please provide file(s)/folder(s) to the --payload argument'
        logger.error(msg)
        sys.exit(1)

    # Set console logging to a minimal if user wants it
    if args.quiet:
        streamhandler.setLevel(logging.WARNING)
        logger.info('Quiet console stream logging enabled.')

    return args


def main():
    pm.COMMANDLINE = True
    args = parse_args()

    pwd = None

    try:
        if not args.free:
            if KEYRING:
                pwd = keyring.get_password('pyfilemail', args.username)

            elif pm.NETRC:
                machine = pm._netrc.authenticators(args.username)
                if machine:
                    pwd = machine[2]

                else:
                    pwd = None

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
            downloads=args.downloads,
            password=args.password,
            checksum=args.checksum,
            zip_=args.compress
            )

        transfer.add_files(args.payload)

        res = transfer.send()

        if res.status_code == 200:
            msg = '\nTransfer complete!'
            logger.info(msg)

    except KeyboardInterrupt:
        msg = '\nAborted by user!'
        logger.warning(msg)
