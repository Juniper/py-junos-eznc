# stdlib
from functools import wraps
import re

from jnpr.junos.exception import RpcError
from jnpr.junos import jxml as JXML


def timeoutDecorator(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if 'dev_timeout' in kwargs:
            try:
                dev = args[0].dev
            except:
                dev = args[0]
            restore_timeout = dev.timeout
            dev.timeout = kwargs.pop('dev_timeout', None)
            try:
                result = function(*args, **kwargs)
                dev.timeout = restore_timeout
                return result
            except Exception:
                dev.timeout = restore_timeout
                raise
        else:
            try:
                return function(*args, **kwargs)
            except Exception:
                raise

    return wrapper


def normalizeDecorator(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if 'normalize' in kwargs:
            normalize = kwargs.pop('normalize', None)
            try:
                dev = args[0].dev
            except:
                dev = args[0]

            if dev._normalize != normalize:
                restore_transform = dev.transform

                if normalize is False:
                    try:
                        dev.transform = dev._nc_transform
                        result = function(*args, **kwargs)
                        dev.transform = restore_transform
                        return result
                    except Exception:
                        dev.transform = restore_transform
                        raise
                else:
                    try:
                        dev.transform = dev._norm_transform
                        result = function(*args, **kwargs)
                        dev.transform = restore_transform
                        return result
                    except Exception:
                        dev.transform = restore_transform
                        raise
            else:
                try:
                    return function(*args, **kwargs)
                except Exception:
                    raise
        else:
            try:
                return function(*args, **kwargs)
            except Exception:
                raise

    return wrapper


def ignoreWarnDecorator(function):
    """
    Ignore warning if ignore_warning provided and the rpc-reply severity level
    is warning

    For example::
        dev.rpc.get(ignore_warning=True)
        dev.rpc.get(ignore_warning='vrrp subsystem not running')
        dev.rpc.get(ignore_warning=['vrrp subsystem not running', 'statement not found'])
        cu.load(cnf, ignore_warning='statement not found')

    :ignore_warning: It can take take boolean value or string or list of string.
        if True, it will ignore all warning. If string, it will ignore warning if
        the statement matches given string. If list of strings, it will try to check
        if warning statement is from any of the given strings in the list:
    """
    @wraps(function)
    def wrapper(*args, **kwargs):
        if 'ignore_warning' in kwargs:
            ignore_warn = kwargs.pop('ignore_warning')
            try:
                result = function(*args, **kwargs)
                return result
            except RpcError as ex:
                ex.rpc_xml = JXML.remove_namespaces(ex.rpc_xml)
                if hasattr(ex, 'rpc_error') and\
                        ex.rpc_error['severity'] == 'warning':
                    if ignore_warn is True:
                        return ex.rpc_xml
                    elif isinstance(ignore_warn, (str, unicode)):
                        if re.search(ignore_warn, ex.message, re.I):
                            return ex.rpc_xml
                    elif isinstance(ignore_warn, list):
                        for warn_msg in ignore_warn:
                            if re.search(warn_msg, ex.message, re.I):
                                return ex.rpc_xml
                    raise ex
                else:
                    raise ex
        else:
            return function(*args, **kwargs)

    return wrapper
