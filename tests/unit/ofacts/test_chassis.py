__author__ = "Nitin Kumar, Rick Sherman"
__credits__ = "Jeremy Schulman"

import unittest
import nose2
from mock import patch, MagicMock
from lxml import etree
import os

from jnpr.junos import Device
from jnpr.junos.ofacts.chassis import facts_chassis as chassis
from jnpr.junos.exception import ConnectNotMasterError
from jnpr.junos.exception import RpcError

from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession


class TestChassis(unittest.TestCase):
    @patch("ncclient.manager.connect")
    @patch("jnpr.junos.device.warnings")
    def setUp(self, mock_warnings, mock_connect):
        mock_connect.side_effect = self._mock_manager
        self.dev = Device(
            host="1.1.1.1",
            user="rick",
            password="password123",
            gather_facts=False,
            fact_style="old",
        )
        self.dev.open()
        self.facts = {}

    @patch("jnpr.junos.Device.execute")
    def test_2RE_true(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        chassis(self.dev, self.facts)
        self.assertTrue(self.facts["2RE"])

    def test_chassis_exception_ConnectNotMasterError(self):
        xmldata = etree.XML("<rpc-reply><output>test</output></rpc-reply>")
        self.dev.rpc.get_chassis_inventory = MagicMock(side_effect=xmldata)
        self.assertRaises(ConnectNotMasterError, chassis, self.dev, self.facts)

    def test_chassis_exception_RuntimeError(self):
        xmldata = etree.XML("<rpc-reply><error>test</error></rpc-reply>")
        self.dev.rpc.get_chassis_inventory = MagicMock(side_effect=xmldata)
        self.assertRaises(RuntimeError, chassis, self.dev, self.facts)

    def test_chassis_exception_RpcError(self):
        xmldata = etree.XML("<rpc-reply><chassis-inventory/></rpc-reply>")
        self.dev.rpc.get_chassis_inventory = MagicMock(side_effect=xmldata)
        self.assertRaises(RpcError, chassis, self.dev, self.facts)

    def _read_file(self, fname):
        from ncclient.xml_ import NCElement

        fpath = os.path.join(os.path.dirname(__file__), "rpc-reply", fname)
        foo = open(fpath).read()

        rpc_reply = NCElement(
            foo, self.dev._conn._device_handler.transform_reply()
        )._NCElement__doc[0]
        return rpc_reply

    def _mock_manager(self, *args, **kwargs):
        if kwargs:
            device_params = kwargs["device_params"]
            device_handler = make_device_handler(device_params)
            session = SSHSession(device_handler)
            return Manager(session, device_handler)

        if args:
            return self._read_file("chassis_" + args[0].tag + ".xml")
