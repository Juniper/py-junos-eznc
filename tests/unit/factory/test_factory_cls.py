__author__ = "Rick Sherman"
__credits__ = "Jeremy Schulman"

import unittest
import nose2

from jnpr.junos.factory.factory_cls import FactoryCfgTable, FactoryOpTable
from jnpr.junos.factory.factory_cls import FactoryTable, FactoryView


class TestFactoryCls(unittest.TestCase):
    def test_factory_cls_cfgtable(self):
        t = FactoryCfgTable()
        self.assertEqual(t.__module__, "jnpr.junos.factory.CfgTable")

    def test_factory_cls_optable(self):
        t = FactoryOpTable("test")
        self.assertEqual(t.__module__, "jnpr.junos.factory.OpTable")

    def test_factory_cls_factorytable(self):
        t = FactoryTable("test")
        self.assertEqual(t.__module__, "jnpr.junos.factory.Table")

    def test_factory_cls_factoryview(self):
        x = FactoryCfgTable()
        x.FIELDS = {"test": "test"}
        x.GROUPS = x.FIELDS
        t = FactoryView(x.FIELDS, extends=x, groups=x.FIELDS)
        self.assertEqual(t.__module__, "jnpr.junos.factory.View")
