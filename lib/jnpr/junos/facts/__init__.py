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
import sys

import jnpr.junos.facts.current_re
import jnpr.junos.facts.domain
import jnpr.junos.facts.ethernet_mac_table
import jnpr.junos.facts.file_list
import jnpr.junos.facts.get_chassis_cluster_status
import jnpr.junos.facts.get_chassis_inventory
import jnpr.junos.facts.get_route_engine_information
import jnpr.junos.facts.get_software_information
import jnpr.junos.facts.get_virtual_chassis_information
import jnpr.junos.facts.ifd_style
import jnpr.junos.facts.iri_mapping
import jnpr.junos.facts.personality
import jnpr.junos.facts.swver
import jnpr.junos.facts.is_linux


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
    for (name, module) in sys.modules.items():
        if name.startswith("jnpr.junos.facts.") and module is not None:
            new_doc_strings = module.provides_facts()
            for key in new_doc_strings:
                if key not in callbacks:
                    callbacks[key] = module.get_facts
                    doc_strings[key] = new_doc_strings[key]
                else:
                    raise RuntimeError(
                        "Both the %s module and the %s module "
                        "claim to provide the %s fact. Please "
                        "report this error."
                        % (callbacks[key].__module__, module.__name__, key)
                    )
    return (callbacks, doc_strings)


# Import all of the fact modules and build the callbacks and doc strings
(_callbacks, _doc_strings) = _build_fact_callbacks_and_doc_strings()

# In case optimization flag is enabled, it strips of docstring and __doc__ becomes None
if __doc__ is None:
    __doc__ = ""

# Append the doc string (__doc__) with the documentation for each fact.
for key in sorted(_doc_strings, key=lambda s: s.lower()):
    __doc__ += ":%s:\n  %s\n" % (key, _doc_strings[key])
