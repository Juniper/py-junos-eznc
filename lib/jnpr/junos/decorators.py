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
            print restore_timeout
            dev._conn.timeout = kwargs['dev_timeout']
            print dev._conn.timeout
            kwargs.pop('dev_timeout', None)
            try:
                result = self.function(*args, **kwargs)
                dev._conn.timeout = restore_timeout
                print dev._conn.timeout
                return result
            except Exception:
                dev._conn.timeout = restore_timeout
                print dev._conn.timeout
                raise
        else:
            try:
                print 'default timeout'
                return self.function(*args, **kwargs)
            except Exception:
                raise

    def __get__(self, obj_self, objtype):
        return functools.partial(self.__call__, obj_self)
