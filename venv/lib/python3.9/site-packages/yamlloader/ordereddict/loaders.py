"""Loaders for `:py:class:~collections.OrderedDict`."""

from __future__ import annotations

from collections import OrderedDict

import yaml

from .. import settings

__all__ = []


def construct_yaml_map(self, node):
    data = OrderedDict()
    yield data
    value = self.construct_mapping(node)
    data.update(value)


def construct_mapping(self, node, deep=False):
    if isinstance(node, yaml.MappingNode):
        self.flatten_mapping(node)
    else:
        msg = f"Expected a mapping node, but found {node.id}"
        raise yaml.constructor.ConstructorError(None, None, msg, node.start_mark)

    mapping = OrderedDict()

    for key_node, value_node in node.value:
        key = self.construct_object(key_node, deep=deep)
        try:
            hash(key)
        except TypeError as err:
            msg = "while constructing a mapping"
            raise yaml.constructor.ConstructorError(
                msg,
                node.start_mark,
                f"found unacceptable key ({err})",
                key_node.start_mark,
            ) from err
        value = self.construct_object(value_node, deep=deep)
        mapping[key] = value
    return mapping


class OrderedLoaderMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_constructor("tag:yaml.org,2002:map", type(self).construct_yaml_map)
        self.add_constructor("tag:yaml.org,2002:omap", type(self).construct_yaml_map)

    construct_yaml_map = construct_yaml_map
    construct_mapping = construct_mapping


class Loader(OrderedLoaderMixin, yaml.Loader):
    pass


class SafeLoader(OrderedLoaderMixin, yaml.SafeLoader):
    pass


if not hasattr(yaml, "CLoader") and settings.ALLOW_NON_C_FALLBACK:
    yaml.CLoader = yaml.Loader


class CLoader(OrderedLoaderMixin, yaml.CLoader):
    pass


if not hasattr(yaml, "CSafeLoader") and settings.ALLOW_NON_C_FALLBACK:
    yaml.CSafeLoader = yaml.SafeLoader


class CSafeLoader(OrderedLoaderMixin, yaml.CSafeLoader):
    pass
