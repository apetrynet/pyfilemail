class FileMailBaseError(Exception):
    def __str__(self):
        return self.message


class FMBaseError(Exception):
    pass


class FMConfigError(FMBaseError):
    pass


class FMFileError(FMBaseError):
    pass


def hellraiser(response):
    _errors = {
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

    if not isinstance(response, dict):
        response_dict = response.json()
    else:
        response_dict = response

    errorcode = response_dict['errorcode']
    errormessage = response_dict['errormessage']

    error = type(_errors[errorcode],
                 (FileMailBaseError,),
                 dict(status=errorcode, message=errormessage)
                 )

    raise error
