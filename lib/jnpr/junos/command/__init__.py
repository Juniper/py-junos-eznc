import os
import sys
from importlib.abc import Loader, MetaPathFinder
from importlib.util import spec_from_loader

import yaml
from jnpr.junos.factory.factory_loader import FactoryLoader
from yamlloader import ordereddict

__all__ = []


class _CommandMetaPathFinder(MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        mod = fullname.split(".")[-1]
        if mod in [
            os.path.splitext(i)[0] for i in os.listdir(os.path.dirname(__file__))
        ]:
            return spec_from_loader(fullname, MetaPathLoader(fullname))


class MetaPathLoader(Loader):
    def __init__(self, fullname):
        self.fullname = fullname
        self.modules = {}

    def exec_module(self, module):
        if self.fullname in self.modules:
            return self.modules[self.fullname]

        mod = self.fullname.split(".")[-1]
        with open(os.path.join(os.path.dirname(__file__), mod + ".yml"), "r") as stream:
            try:
                modules = FactoryLoader().load(
                    yaml.load(stream, Loader=ordereddict.Loader)
                )
            except yaml.YAMLError as exc:
                raise ImportError("%s is not loaded" % mod)

        for k, v in modules.items():
            setattr(module, k, v)

        self.modules[self.fullname] = module

        return module


sys.meta_path.insert(0, _CommandMetaPathFinder())
