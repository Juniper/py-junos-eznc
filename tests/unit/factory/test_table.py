__author__ = "Rick Sherman, Nitin Kumar"
__credits__ = "Jeremy Schulman"

import unittest
from nose.plugins.attrib import attr
import os

from jnpr.junos import Device
from jnpr.junos.factory.table import Table

from mock import patch
from lxml import etree
from jnpr.junos.op.phyport import PhyPortTable

from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession
from ncclient.devices.junos import JunosDeviceHandler
import sys

if sys.version < "3":
    builtin_string = "__builtin__"
else:
    builtin_string = "builtins"


@attr("unit")
class TestFactoryTable(unittest.TestCase):
    @patch("ncclient.manager.connect")
    def setUp(self, mock_connect):
        mock_connect.side_effect = self._mock_manager
        self.dev = Device(
            host="1.1.1.1", user="rick", password="password123", gather_facts=False
        )
        self.device_handler = JunosDeviceHandler(
            device_params={"name": "junos", "local": False}
        )
        self.dev.open()
        self.table = Table(dev=self.dev)
        self.ppt = PhyPortTable(self.dev)

    def test_config_constructor(self):
        self.assertTrue(isinstance(self.table.D, Device))

    def test_table_hostname(self):
        self.assertEqual(self.table.hostname, "1.1.1.1")

    def test_table_is_container(self):
        self.assertTrue(self.table.is_container)

    def test_table_repr_xml_none(self):
        self.assertEqual(repr(self.table), "Table:1.1.1.1 - Table empty")

    def test_table_view_setter_ValueError(self):
        try:
            self.table.view = "test"
        except Exception as ex:
            self.assertEqual(ex.__class__, ValueError)

    @patch("jnpr.junos.Device.execute")
    def test_keys_RuntimeError(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.ppt.get("ge-0/0/0")
        self.ppt.ITEM_NAME_XPATH = 1
        self.assertRaises(RuntimeError, self.ppt.keys)

    @patch("jnpr.junos.Device.execute")
    def test_keys__keys_composite(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.ppt.get("ge-0/0/0")
        self.ppt.ITEM_NAME_XPATH = ["name", "missing", "mtu"]
        self.assertEqual(
            self.ppt.keys(), [("ge-0/0/0", None, "1514"), ("ge-0/0/1", None, "1514")]
        )

    @patch("jnpr.junos.Device.execute")
    def test_keys__keys_pipe(self, mock_execute):
        from jnpr.junos.op.lldp import LLDPNeighborTable

        mock_execute.side_effect = self._mock_manager
        self.lldp = LLDPNeighborTable(self.dev)
        self.lldp.get()
        self.assertEqual(self.lldp.keys(), ["et-0/0/48", "et-0/0/49", "xe-0/0/13"])

    @patch("jnpr.junos.Device.execute")
    def test_table_repr_xml_not_none(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.ppt.get("ge-0/0/0")
        self.table.xml = self.ppt.xml
        self.table.ITEM_XPATH = self.ppt.ITEM_XPATH
        self.assertEqual(repr(self.table), "Table:1.1.1.1: 2 items")

    @patch("jnpr.junos.Device.execute")
    def test_table_get_keys_values(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.ppt.get("ge-0/0/0")
        self.assertEqual(self.ppt.keys(), ["ge-0/0/0", "ge-0/0/1"])
        self.assertEqual(len(self.ppt.values()), 2)
        self.ppt.view = None
        self.assertEqual(len(self.ppt.values()), 2)

    @patch("jnpr.junos.Device.execute")
    def test_table__getitem__(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.ppt.get("ge-0/0/0")
        self.assertEqual(self.ppt[0].ITEM_NAME_XPATH, "name")

    @patch("jnpr.junos.Device.execute")
    def test_table__getitem__slice(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.ppt.get("ge-0/0/0")
        self.assertEqual(self.ppt[:1][0].__class__.__name__, "PhyPortView")

    @patch("jnpr.junos.Device.execute")
    def test_table__getitem__tuple(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.ppt.get("ge-0/0/0")
        self.assertEqual(self.ppt[("ge-0/0/0",)], None)

    @patch("jnpr.junos.Device.execute")
    def test_table__contains__(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.ppt.get("ge-0/0/0")
        self.assertTrue("ge-0/0/0" in self.ppt)

    @patch("jnpr.junos.Device.execute")
    def test_table_items(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.ppt.get("ge-0/0/0")
        self.assertEqual(len(self.ppt.items()[1][1]), 8)

    def test_table_get_return_none(self):
        self.assertEqual(self.table.get("ge-0/0/0"), None)

    def test_table_get_RuntimeError(self):
        self.assertRaises(RuntimeError, self.table._keys)

    @patch("jnpr.junos.Device.execute")
    @patch(builtin_string + ".open")
    def test_table_savexml(self, mock_file, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.ppt.xml = etree.XML("<root><a>test</a></root>")
        self.ppt.savexml("foo.xml", hostname=True, append="test")
        mock_file.assert_called_once_with("foo_1.1.1.1_test.xml", "wb+")
        self.ppt.savexml("foo.xml", hostname=True, timestamp=True)
        self.assertEqual(mock_file.call_count, 2)

    def _read_file(self, fname):
        from ncclient.xml_ import NCElement

        fpath = os.path.join(os.path.dirname(__file__), "rpc-reply", fname)
        foo = open(fpath).read()

        rpc_reply = NCElement(
            foo, self.device_handler.transform_reply()
        )._NCElement__doc[0]
        return rpc_reply

    def _mock_manager(self, *args, **kwargs):
        if kwargs:
            if args and ("normalize" in kwargs or "filter_xml" in kwargs):
                return self._read_file(args[0].tag + ".xml")
            device_params = kwargs["device_params"]
            device_handler = make_device_handler(device_params)
            session = SSHSession(device_handler)
            return Manager(session, device_handler)

        if args:
            return self._read_file(args[0].tag + ".xml")
