import warnings
from pprint import pformat

try:
    from collections.abc import MutableMapping
except ImportError:
    from collections import MutableMapping

import jnpr.junos.facts
from jnpr.junos.facts import __doc__ as facts_doc
import jnpr.junos.exception


class _FactCache(MutableMapping):
    """
    A dictionary-like object which performs on-demand fact gathering.

    This class should not be used directly. An instance of this class is
    available as the :attr:`facts` attribute of a Device object.

    **Dictionary magic methods:**
      * :meth:`__getitem__`: Gets the value of a given key in the dict.
      * :meth:`__delitem__`: Called when a key is deleted from the dict.
      * :meth:`__setitem__`: Called when a key is set on the dict.
      * :meth:`__iter__`: Called when iterating over the keys of the dict.
      * :meth:`__len__`: Called when getting the length of the dict.
      * :meth:`__repr__`: Called when representing the dict as a string.

    **Additional methods:**
      * :meth:`_refresh`: Refreshes the fact cache.
    """

    def __init__(self, device):
        """
        _FactCache object constructor.

        :param device: The device object for which fact gathering will be
          performed.
        """
        self._device = device
        self._cache = dict()
        self._call_stack = list()
        self._callbacks = jnpr.junos.facts._callbacks
        self._exception_on_failure = False
        self._warnings_on_failure = False
        self._should_warn = False

    def __getitem__(self, key):
        """
        Return the value of a particular key in the dictionary.

        If the fact has already been cached, the value is simply returned from
        the cache. If the value has not been cached, then the appropriate
        callback function is invoked to gather the fact from the device. The
        value is cached, and then returned.

        If _warnings_on_failure is True, then a warning is logged if there is
        an error gathering a fact from the device.

        :param key: The key who's value is returned.

        :returns value: The value of the key fact. If key is a known fact, but
            there is an error gathering the fact, then the value None is
            returned.

        :raises KeyError:
            When key is not a known fact (there is no callback present to
            gather the fact.)

        :raises jnpr.junos.exception.FactLoopError:
            When there is a loop attempting to gather the fact.

        :raises other exceptions as defined by the fact gathering modules:
            When an error is encountered and _exception_on_failure is True.
        """
        if key not in self._callbacks:
            # Not a fact that we know how to provide.
            raise KeyError(
                "%s: There is no function to gather the %s fact" % (key, key)
            )
        if key not in self._cache:
            # A known fact, but not yet cached. Go get it and cache it.
            if self._callbacks[key] in self._call_stack:
                raise jnpr.junos.exception.FactLoopError(
                    "A loop was detected while gathering the %s fact. The %s "
                    "module has already been called. Please report this error."
                    % (key, self._callbacks[key].__module__)
                )
            else:
                # Add the callback we are about to invoke to the _call_stack in
                # order to detect loops in fact gathering.
                self._call_stack.append(self._callbacks[key])
            try:
                # Invoke the callback
                new_facts = self._callbacks[key](self._device)
            except jnpr.junos.exception.FactLoopError:
                raise
            except Exception:
                # An exception was raised. No facts were returned.
                # Raise the exception to the user?
                if self._exception_on_failure:
                    raise
                # Warn the user?
                if self._warnings_on_failure:
                    self._should_warn = True
                # Set all of the facts which should have been returned
                # by this callback to the default value of None.
                for new_key in self._callbacks:
                    if self._callbacks[key] is self._callbacks[new_key]:
                        self._cache[new_key] = None
            else:
                # No exception
                for new_key in new_facts:
                    if (
                        new_key not in self._callbacks
                        or self._callbacks[key] is not self._callbacks[new_key]
                    ):
                        # The callback returned a fact it didn't advertise
                        raise RuntimeError(
                            "The %s module returned the %s "
                            "fact, but does not list %s as a "
                            "provided fact. Please report this "
                            "error."
                            % (self._callbacks[key].__module__, new_key, new_key)
                        )
                    else:
                        # Cache the returned fact
                        self._cache[new_key] = new_facts[new_key]
            finally:
                # Always pop the current callback from _call_stack,
                # regardless of whether or not an exception was raised.
                self._call_stack.pop()
        if key in self._cache:
            # key fact is cached. Return it.
            if self._device._fact_style == "both":
                # Compare old and new-style values.
                if key in self._device._ofacts:
                    # Skip key comparisons for certain keys.
                    #
                    # The old facts gathering code has an up_time key.
                    # The new facts gathering code maintains this key for RE0
                    # and RE1 facts, but it's not comparable (because it
                    # depends on when the fact was gathered and is therefore
                    # not really a "fact".) The new re_info fact omits the
                    # up_time field for this reason.
                    #
                    # The old facts gathering code didn't return a correct
                    # value for the master fact when the system was a VC.
                    # The new fact gathering code still returns the master fact
                    # but returns a correct value for VCs. It also returns a
                    # new re_master fact which is much more useful.
                    if key not in ["RE0", "RE1", "master"]:
                        if self._cache[key] != self._device._ofacts[key]:
                            warnings.warn(
                                "New and old-style facts do not "
                                "match for the %s fact.\n"
                                "    New-style value: %s\n"
                                "    Old-style value: %s\n"
                                % (key, self._cache[key], self._device._ofacts[key]),
                                RuntimeWarning,
                            )
            return self._cache[key]
        else:
            # key fact was not returned by callback
            raise RuntimeError(
                "The %s module claims to provide the %s "
                "fact, but failed to return it. Please report "
                "this error." % (self._callbacks[key].__module__, key)
            )

    def __delitem__(self, key):
        """
        Facts are read-only. Don't allow deleting an item.
        """
        raise RuntimeError("facts are read-only!")

    def __setitem__(self, key, value):
        """
        Facts are read-only. Don't allow setting an item.
        """
        raise RuntimeError("facts are read-only!")

    def __iter__(self):
        """
        An iterator of known facts.

        :returns iterator: of all of the 'non-hidden' facts we know how to
        gather, regardless of whether or not they've already been cached. Fact
        names which are hidden start with an underscore and are not returned.
        """
        callbacks = {}
        for key in self._callbacks:
            if not key.startswith("_"):
                callbacks[key] = self._callbacks[key]
        return iter(callbacks)

    def __len__(self):
        """
        The length of all known facts.

        :returns length: of all of the facts we know how to gather,
        regardless of whether or not they've already been cached.
        """
        return len(self._callbacks)

    def __str__(self):
        """
        A string representation of the facts dictionary.

        :returns string: a string representation of the dictionary.
          Because this returns the value of every fact, it has the
          side-effect of causing any ungathered facts to be gathered and then
          cached.
        """
        string = ""
        for key in sorted(self):
            if not key.startswith("_"):
                current = "'%s': %s" % (key, repr(self.get(key)))
                if string:
                    string = ", ".join([string, current])
                else:
                    string = current
        return "{" + string + "}"

    def __repr__(self):
        """
        A formated string representation of the facts dictionary.

        :returns string: a formated string representation of the dictionary.
          Because this returns the value of every fact, it has the
          side-effect of causing any ungathered facts to be gathered and then
          cached.
        """
        return pformat(dict(self))

    def _refresh(
        self, exception_on_failure=False, warnings_on_failure=False, keys=None
    ):
        """
        Empty the cache to force a refresh of one or more facts.

        Empties the fact gathering cache for all keys (if keys == None) or a
        set of keys. This causes the fact to be gathered and cached upon next
        access. If either eception_on_failure or warnings_on_failure is true,
        then all facts are accessed by getting the string representation of the
        facts. This causes all facts to immediately be populated so that any
        exceptions or warnings are generated during the call to _refresh().

        :param exception_on_failure: A boolean which indicates if an exception
          should be raised upon a failure gathering facts.

        :param warnings_on_failure: A boolean which indicates if an warning
          should be logged upon a failure gathering facts.

        :param keys: A single key as a string, or an iterable of keys (such
          as a list, set, or or tuple.) The specified keys are emptied from
          the cache. If None, all keys are emptied from the cache.

        :raises RuntimeError:
            When keys contains an unknown fact.
        """
        refresh_keys = None
        if keys is not None:
            if isinstance("str", type(keys)):
                refresh_keys = (keys,)
            else:
                refresh_keys = keys
        if refresh_keys is not None:
            for key in refresh_keys:
                if key in self._callbacks:
                    if key in self._cache:
                        del self._cache[key]
                else:
                    raise RuntimeError(
                        "The %s fact can not be refreshed. %s "
                        "is not a known fact." % (key, key)
                    )
        else:
            self._cache = dict()
        if exception_on_failure or warnings_on_failure:
            self._exception_on_failure = exception_on_failure
            self._warnings_on_failure = warnings_on_failure
            try:
                str(self._device.facts)
            except Exception:
                if exception_on_failure:
                    raise
            finally:
                if warnings_on_failure and self._should_warn:
                    warnings.warn(
                        "Facts gathering is incomplete. "
                        "To know the reason call "
                        '"dev.facts_refresh('
                        'exception_on_failure=True)"',
                        RuntimeWarning,
                    )
                self._exception_on_failure = False
                self._warnings_on_failure = False
                self._should_warn = False

    # In case optimization flag is enabled, it strips of docstring and __doc__ becomes None
    if __doc__ is None:
        __doc__ = ""

    # Precede the class's documentation with the documentation on the specific
    # facts from  the jnpr.junos.facts package.
    __doc__ = facts_doc + "Implementation details on the _FactCache class:" + __doc__
