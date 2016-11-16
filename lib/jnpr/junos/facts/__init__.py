"""
Docstring to be replaced by __doc__
"""
import importlib
import os
import sys

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
        if (os.path.isfile(os.path.join(facts_dir,file)) and
            not os.path.islink(os.path.join(facts_dir,file))):
            if file.endswith('.py') and not file.startswith('_'):
                (module_name,_) = file.rsplit('.py',1)
                module_names.append('%s.%s' % (__name__,module_name))
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
                raise RuntimeError('Both the %s module and the %s module claim '
                                   'to provide the %s fact. Please report this '
                                   ' error.' %
                                   (callbacks[key].__module__,
                                    module.__name__,
                                    key))
    return (callbacks, doc_strings)

# Replaces the doc string defined at the top of this module file.
__doc__ = """
PyEZ maintains a dictionary of read-only facts about the Junos device.

These facts are accessed as a dictionary on the `facts` attribute of a `Device`
object instance. For example, if `dev` is an instance of a `Device` object,
the hostname of the device can be accessed with:
  `dev.facts['hostname']`

Force a refresh of all facts with:
  `dev.facts_refresh()`
Force a refresh of a single fact with:
  `dev.facts_refresh(keys='hostname')`
Force a refresh of a set of facts with:
  `dev.facts_refresh(keys=('hostname','domain','fqdn'))`

The following dictionary keys represent the available facts and their meaning:

"""

# Import all of the fact modules and build the callbacks and doc strings
(_callbacks,_doc_strings) = _build_fact_callbacks_and_doc_strings()

# Append the doc string with the documentation for each fact.
for key in sorted(_doc_strings,cmp=lambda a,b: cmp(a.lower(), b.lower())):
    __doc__ += ':%s:\n  %s\n' % (key,_doc_strings[key])