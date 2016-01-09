# -*- coding: utf-8 -*-
from re import search


def validString(value):
    """
    Check if provided attribute is a string type.

    :param value: to check if valid

    :returns: `Boolean`
    """

    if not isinstance(value, basestring):
        return False

    return True


def validEmail(email):
    """
    Check for valid formatted email address.

    :param email:

    :returns: `Boolean`
    """

    if not validString(email):
        return False

    res = search('(\w+[\.]?)+@(\w+[\.]?)+', email)
    if not res:
        return False

    return True
