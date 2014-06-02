__author__ = "Rick Sherman"
__credits__ = "Jeremy Schulman"

import unittest
from nose.plugins.attrib import attr

from jnpr.junos import Device
from jnpr.junos.factory.table import Table

from mock import MagicMock, patch


@attr('unit')
class TestFactoryTable(unittest.TestCase):
    def setUp(self):
        self.dev = Device(host='1.1.1.1')
        self.table = Table(dev=self.dev)

    def test_config_constructor(self):
        self.assertTrue(isinstance(self.table.D, Device))
