import collections
import jnpr.junos.nfacts

class _FactCache(collections.MutableMapping):
    """

    """
    def __init__(self,device):
        self._device = device
        self._cache = dict()
        self._callbacks = jnpr.junos.nfacts._callbacks

    def __getitem__(self, key):
        if key not in self._callbacks:
            # Not a fact that we know how to provide.
            raise KeyError
        if key not in self._cache:
            # A known fact, but not yet cached. Go get it and cache it.
            new_facts = self._callbacks[key](self._device)
            for new_key in new_facts:
                if (new_key not in self._callbacks or
                    self._callbacks[key] is not self._callbacks[new_key]):
                    # The callback returned a fact it didn't advertise
                    raise RuntimeError("The %s() function returned the %s "
                                       "fact, but does not list %s as a "
                                       "provided fact. Please report this "
                                       "error." %
                                       (self._callbacks[new_key],
                                        new_key,
                                        new_key))
                else:
                    # Cache the returned fact
                    self._cache[new_key] = new_facts[new_key]
        if key in self._cache:
            # key fact is cached. Return it.
            return self._cache[key]
        else:
            # key fact was not returned by callback
            raise RuntimeError("The %s() function claims to provide the %s "
                               "fact, but failed to return it. Please report "
                               "this error." % (self._callbacks[key], key))

    def __delitem__(self, key):
        raise RuntimeError("facts are read-only!")

    def __setitem__(self, key, value):
        raise RuntimeError("facts are read-only!")

    def __iter__(self):
        return iter(self._callbacks)

    def __len__(self):
        return len(self._callbacks)