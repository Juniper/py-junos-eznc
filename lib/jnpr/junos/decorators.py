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
    @wraps(function)
    def wrapper(*args, **kwargs):
        if 'ignore_warning' in kwargs or 'ignore_warning_message' in kwargs:
            ignore_warn_msg = kwargs.pop('ignore_warning_message', None)
            ignore_warn = kwargs.pop('ignore_warning', None) or \
                          ignore_warn_msg is not None
            if ignore_warn is True:
                try:
                    result = function(*args, **kwargs)
                    return result
                except RpcError as ex:
                    ex.xml = JXML.remove_namespaces(ex.xml)
                    if hasattr(ex, 'rpc_error') and\
                                    ex.rpc_error['severity'] == 'warning':
                        if ignore_warn_msg is None:
                            return ex.xml
                        elif isinstance(ignore_warn_msg, (str, unicode)):
                            if re.search(ignore_warn_msg, ex.message, re.I):
                                return ex.xml
                        elif isinstance(ignore_warn_msg, list):
                            for warn_msg in ignore_warn_msg:
                                if re.search(warn_msg, ex.message, re.I):
                                    return ex.xml
                        raise ex
                    else:
                        raise ex
                except Exception:
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