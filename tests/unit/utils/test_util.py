__author__ = "Nitin Kumar, Rick Sherman"
__credits__ = "Jeremy Schulman"

import unittest
from nose.plugins.attrib import attr

from jnpr.junos import Device
from jnpr.junos.utils.util import Util

from mock import patch


@attr('unit')
class TestUtil(unittest.TestCase):

    @patch('ncclient.manager.connect')
    def setUp(self, mock_connect):
        self.dev = Device(host='1.1.1.1', user='nitin', password='password123',
                          gather_facts=False)
        self.dev.open()
        self.util = Util(self.dev)

    def test_repr(self):
        self.assertEqual(repr(self.util), 'jnpr.junos.utils.Util(1.1.1.1)')

    def test_dev_setter_exception(self):
        def mod_dev():
            self.util.dev = 'abc'
        self.assertRaises(RuntimeError, mod_dev)

    def test_rpc_setter_exception(self):
        def mod_rpc():
            self.util.rpc = 'abc'
        self.assertRaises(RuntimeError, mod_rpc)
