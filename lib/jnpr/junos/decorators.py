# stdlib
import functools


class timeoutDecorator(object):
    def __init__(self, function):
        self.function = function
        self.__doc__ = function.__doc__
        self.__name__ = function.__name__
        self.__module__ = function.__module__

    def __call__(self, *args, **kwargs):
        if 'dev_timeout' in kwargs:
            try:
                dev = args[0].dev
            except:
                dev = args[0]
            restore_timeout = dev._conn.timeout
            dev._conn.timeout = kwargs['dev_timeout']
            kwargs.pop('dev_timeout', None)
            try:
                result = self.function(*args, **kwargs)
                dev._conn.timeout = restore_timeout
                return result
            except Exception:
                dev._conn.timeout = restore_timeout
                raise
        else:
            try:
                return self.function(*args, **kwargs)
            except Exception:
                raise

    def __get__(self, obj_self, objtype):
        return functools.partial(self.__call__, obj_self)
