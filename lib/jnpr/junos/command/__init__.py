import sys
import os
import yaml
import types

from jnpr.junos.factory.factory_loader import FactoryLoader

import yamlordereddictloader

__all__ = []


class MetaPathFinder(object):
    def find_module(self, fullname, path=None):
        mod = fullname.split(".")[-1]
        if mod in [
            os.path.splitext(i)[0] for i in os.listdir(os.path.dirname(__file__))
        ]:
            return MetaPathLoader()


class MetaPathLoader(object):
    def load_module(self, fullname):
        if fullname in sys.modules:
            return sys.modules[fullname]
        mod = fullname.split(".")[-1]
        modObj = types.ModuleType(
            mod, "Module created to provide a context for %s" % mod
        )
        with open(os.path.join(os.path.dirname(__file__), mod + ".yml"), "r") as stream:
            try:
                modules = FactoryLoader().load(
                    yaml.load(stream, Loader=yamlordereddictloader.Loader)
                )
            except yaml.YAMLError as exc:
                raise ImportError("%s is not loaded" % mod)
        for k, v in modules.items():
            setattr(modObj, k, v)
        sys.modules[fullname] = modObj
        return modObj


sys.meta_path.insert(0, MetaPathFinder())
