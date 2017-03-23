"""
A dictionary-like object of read-only facts about the Junos device.

These facts are accessed as the `facts` attribute of a `Device` object
instance. For example, if `dev` is an instance of a `Device` object,
the hostname of the device can be accessed with::

    dev.facts['hostname']

Force a refresh of all facts with::

    dev.facts_refresh()

Force a refresh of a single fact with::

    dev.facts_refresh(keys='hostname')

Force a refresh of a set of facts with::

    dev.facts_refresh(keys=('hostname','domain','fqdn'))

NOTE: The dictionary key for each available fact is guaranteed to exist. If
      there is a problem gathering the value of a specific fact/key, or if
      the fact is not supported on a given platform, then the fact/key will
      have the value None (the None object, not a string.)

      Accessing a dictionary key which does not correspond to an available fact
      will raise a KeyError (the same behavior as accessing a non-existent key
      of a normal dict.)

The following dictionary keys represent the available facts and their meaning:

"""
import importlib
import os


def _get_list_of_fact_module_names():
    """
    Get a list of fact module names.

    Gets a list of the module names that reside in the facts directory (the
    directory where this jnpr.junos.facts.__init__.py file lives). Any module
    names that begin with an underscore (_) are ommitted.

    :returns:
      A list of fact module names.
    """
    module_names = []
    facts_dir = os.path.dirname(__file__)
    for file in os.listdir(facts_dir):
        if (os.path.isfile(os.path.join(facts_dir, file)) and
           not os.path.islink(os.path.join(facts_dir, file))):
            if file.endswith('.py') and not file.startswith('_'):
                (module_name, _) = file.rsplit('.py', 1)
                module_names.append('%s.%s' % (__name__, module_name))
    return module_names


def _import_fact_modules():
    """
    Import each of the modules returned by _get_list_of_fact_module_names().

    :returns:
      A list of the imported module objects.
    """
    modules = []
    for name in _get_list_of_fact_module_names():
        modules.append(importlib.import_module(name))
    return modules


def _build_fact_callbacks_and_doc_strings():
    """
    Imports the fact modules and returns callbacks and doc_strings.

    :returns:
      A tuple of callbacks and doc_strings.
      callbacks - a dict of the callback function to invoke for each fact.
      doc_strings - a dict of the doc string for each fact.

    :raises:
      RuntimeError if more than one module claims to provide the same fact.
                   This is an indication of incorrectly written fact module(s).
                   In order to remain deterministic, each fact must be
                   provided by a single module.
    """
    callbacks = {}
    doc_strings = {}
    for module in _import_fact_modules():
        new_doc_strings = module.provides_facts()
        for key in new_doc_strings:
            if key not in callbacks:
                callbacks[key] = module.get_facts
                doc_strings[key] = new_doc_strings[key]
            else:
                raise RuntimeError('Both the %s module and the %s module '
                                   'claim to provide the %s fact. Please '
                                   'report this error.' %
                                   (callbacks[key].__module__,
                                    module.__name__,
                                    key))
    return (callbacks, doc_strings)


# Import all of the fact modules and build the callbacks and doc strings
(_callbacks, _doc_strings) = _build_fact_callbacks_and_doc_strings()

# Append the doc string (__doc__) with the documentation for each fact.
for key in sorted(_doc_strings, key=lambda s: s.lower()):
    __doc__ += ':%s:\n  %s\n' % (key, _doc_strings[key])
