import collections
import warnings
from abc import ABCMeta

import jnpr.junos.facts
import jnpr.junos.exception

class _FactCache(collections.MutableMapping):
    """

    """
    __metaclass__ = ABCMeta

    def __init__(self,device):
        self._device = device
        self._cache = dict()
        self._callbacks = jnpr.junos.facts._callbacks
        self._exception_on_failure = False
        self._warnings_on_failure = False
        self._should_warn = False

    def __getitem__(self, key):
        if key not in self._callbacks:
            # Not a fact that we know how to provide.
            raise KeyError('%s: There is no function to gather the %s fact' %
                           (key,key))
        if key not in self._cache:
            # A known fact, but not yet cached. Go get it and cache it.
            try:
                new_facts = self._callbacks[key](self._device)
            except Exception as err:
                # An exception was raised. No facts were returned.
                # Raise the exception to the user?
                if self._exception_on_failure:
                    raise
                # Warn the user?
                if self._warnings_on_failure:
                    self._should_warn = True
                # Set all of the facts which should have been returned
                # by this callback to the default value of None.
                current_callback = self._callbacks[key]
                for new_key in self._callbacks:
                    if self._callbacks[key] is self._callbacks[new_key]:
                        self._cache[new_key] = None
            else:
                for new_key in new_facts:
                    if (new_key not in self._callbacks or
                        self._callbacks[key] is not self._callbacks[new_key]):
                        # The callback returned a fact it didn't advertise
                        raise RuntimeError("The %s module returned the %s "
                                           "fact, but does not list %s as a "
                                           "provided fact. Please report this "
                                           "error." %
                                           (self._callbacks[key].__module__,
                                            new_key,
                                            new_key))
                    else:
                        # Cache the returned fact
                        self._cache[new_key] = new_facts[new_key]
        if key in self._cache:
            # key fact is cached. Return it.
            if self._device._fact_style == 'both':
                if key in self._device._ofacts:
                    if self._cache[key] != self._device._ofacts[key]:
                        raise RuntimeError('New and old-style facts do not '
                                           'match for the %s fact.\n'
                                           '    New-style value: %s\n'
                                           '    Old-style value: %s\n' %
                                           (key,
                                            self._cache[key],
                                            self._device._ofacts[key]))
            return self._cache[key]
        else:
            # key fact was not returned by callback
            raise RuntimeError("The %s module claims to provide the %s "
                               "fact, but failed to return it. Please report "
                               "this error." % (self._callbacks[key].__module__,
                                                key))

    def __delitem__(self, key):
        raise RuntimeError("facts are read-only!")

    def __setitem__(self, key, value):
        raise RuntimeError("facts are read-only!")

    def __iter__(self):
        return iter(self._callbacks)

    def __len__(self):
        return len(self._callbacks)

    def __repr__(self):
        string = ''
        for key in self:
            current = "'%s': %s" % (key,repr(self.get(key)))
            if string:
                string = ', '.join([string,current])
            else:
                string = current
        return '{' + string + '}'

    def refresh(self,
                exception_on_failure=False,
                warnings_on_failure=False,
                keys=None):
        """
        """
        refresh_keys = ()
        if keys is not None:
            if isinstance('str',type(keys)):
                refresh_keys = (keys,)
            else:
                refresh_keys = keys
        if refresh_keys:
            for key in refresh_keys:
                if key in self._cache:
                    del self._cache[key]
                else:
                    raise RuntimeError('The %s fact can not be refreshed. %s '
                                       'is not a known fact.' % (key,key))
        else:
            self._cache = dict()
        if exception_on_failure or warnings_on_failure:
            self._exception_on_failure = exception_on_failure
            self._warnings_on_failure = warnings_on_failure
            try:
                _ = str(self._device.facts)
            except Exception:
                if exception_on_failure:
                    raise
                if warnings_on_failure and self._should_warn:
                    warnings.warn('Facts gathering is incomplete. '
                                  'To know the reason call '
                                  '"dev.facts_refresh('
                                  'exception_on_failure=True)"',
                                  RuntimeWarning)
            finally:
                self._exception_on_failure = False
                self._warnings_on_failure = False
                self._should_warn = False

_FactCache.register(dict)