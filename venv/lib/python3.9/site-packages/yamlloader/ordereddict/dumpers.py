"""Dumpers for `:py:class:~collections.OrderedDict`."""

from __future__ import annotations

from collections import OrderedDict

import yaml

from .. import settings

__all__ = []


def represent_ordereddict(self, data):
    """

    Parameters
    ----------
    data : dict, OrderedDict

    Returns
    -------
    mapping
    """
    return self.represent_mapping("tag:yaml.org,2002:map", data.items())


class OrderedDumperMixin:
    def __init__(self, *args, **kwargs):
        sub_doc = self.__doc__
        if sub_doc is None:
            sub_doc = ""
        self.__doc__ = """Dump :py:class:~`collections.OrderedDict` and :py:class:`dict` (py37+)
        to YAML preserving the order."""
        self.__doc__ += sub_doc
        super().__init__(*args, **kwargs)
        self.add_representer(OrderedDict, type(self).represent_ordereddict)

    represent_ordereddict = staticmethod(represent_ordereddict)


doc_extension_Cversion = """

    The C version is preferable over the non-C version as they
    do equivalent things while the C version is faster.
    """


class Dumper(OrderedDumperMixin, yaml.Dumper):
    pass


class SafeDumper(OrderedDumperMixin, yaml.SafeDumper):
    __doc__ = """
    """


if not hasattr(yaml, "CDumper"):
    if settings.ALLOW_NON_C_FALLBACK:
        CDumper = Dumper
else:

    class CDumper(OrderedDumperMixin, yaml.CDumper):
        __doc__ = doc_extension_Cversion


if not hasattr(yaml, "CSafeDumper"):
    if settings.ALLOW_NON_C_FALLBACK:
        CSafeDumper = SafeDumper
else:

    class CSafeDumper(OrderedDumperMixin, yaml.CSafeDumper):
        __doc__ = doc_extension_Cversion
