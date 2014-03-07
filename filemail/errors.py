# -*- coding: utf-8 -*-


class FMBaseError(Exception):
    _error_codes = {
        # General Errors
        1001: 'UnknownError',
        1002: 'InvalidParameter',
        1003: 'InputParameterMissing',
        1004: 'InvalidEmail',
        1005: 'NotFound',

        # Authentication Errors
        2001: 'WrongUsernamePassword',
        2002: 'PasswordTooWeak',
        2003: 'InvalidOrExpiredLoginToken',
        2004: 'AccountExpired',
        2005: 'CaptchaRequiredForNextLogin',
        2006: 'LDAPUnableToCreateUser',
        2007: 'LDAPWrongUsernamePassword',
        2008: 'AccessDenied',

        # Transfer Initialization Errors
        3001: 'BusinessAccountExistsRegistrationRequired',
        3002: 'UserAccountExistsLoginRequired',
        3003: 'Blocked',
        3004: 'AllFileserversBusy',
        3005: 'FreeLimitReached',

        # Transfer File Errors
        4001: 'TransferExpired',
        4002: 'PasswordRequired',
        4003: 'UploadNotComplete',
        4004: 'FileIsDeleted',

        # Subscription / Registration Errors
        5001: 'SubscriptionNotFound',
        5002: 'EmailAlreadyRegistered',
        5003: 'SignupFormNotAccepted',
        5004: 'SessionPasswordNotFound',
        5005: 'SessionCustRefNotFound',
        5006: 'AllUserLicencesesInUse'
        }

    def __init__(self, error_code, message=''):
        self.error_code = error_code
        self.message = message

    def __str__(self):
        error_name = self._error_codes[self.error_code]
        return '{error}: {message}'.format(error=error_name,
                                            message=self.message)


class FMGenericError(FMBaseError):
    pass


class FMAuthenticationError(FMBaseError):
    pass


class FMTransferInitError(FMBaseError):
    pass


class FMTransferFileGetError(FMBaseError):
    pass


class FMSubscriptionError(FMBaseError):
    pass


class FMConfigError(FMBaseError):
    pass