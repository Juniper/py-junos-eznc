# stdlib
from functools import wraps


def timeoutDecorator(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if 'dev_timeout' in kwargs:
            try:
                dev = args[0].dev
            except:
                dev = args[0]
            restore_timeout = dev.timeout
            dev.timeout = kwargs['dev_timeout']
            kwargs.pop('dev_timeout', None)
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
