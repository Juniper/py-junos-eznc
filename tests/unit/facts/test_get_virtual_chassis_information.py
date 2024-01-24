__author__ = "Stacy Smith"
__credits__ = "Jeremy Schulman, Nitin Kumar"

import unittest
import nose2
from mock import patch, MagicMock
import os
import sys
from lxml import etree

from jnpr.junos import Device
from jnpr.junos.exception import RpcError

from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession


class TestGetVirtualChassisInformation(unittest.TestCase):
    @patch("ncclient.manager.connect")
    def setUp(self, mock_connect):
        mock_connect.side_effect = self._mock_manager_setup
        self.dev = Device(
            host="1.1.1.1", user="rick", password="password123", gather_facts=False
        )
        self.dev.open()

    @patch("jnpr.junos.Device.execute")
    def test_vc(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_vc
        self.assertEqual(self.dev.facts["vc_capable"], True)
        self.assertEqual(self.dev.facts["vc_mode"], "Enabled")
        self.assertEqual(self.dev.facts["vc_fabric"], None)
        self.assertEqual(self.dev.facts["vc_master"], "0")

    @patch("jnpr.junos.Device.execute")
    def test_vc_dual_master(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_vc_dual_master
        self.assertEqual(self.dev.facts["vc_capable"], None)
        self.assertEqual(self.dev.facts["vc_mode"], None)
        self.assertEqual(self.dev.facts["vc_fabric"], None)
        self.assertEqual(self.dev.facts["vc_master"], None)

    @patch("jnpr.junos.Device.execute")
    def test_vc_error(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_vc_error
        self.assertEqual(self.dev.facts["vc_capable"], False)
        self.assertEqual(self.dev.facts["vc_mode"], None)
        self.assertEqual(self.dev.facts["vc_fabric"], None)
        self.assertEqual(self.dev.facts["vc_master"], None)

    @patch("jnpr.junos.Device.execute")
    def test_vc_empty(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_vc_empty
        self.assertEqual(self.dev.facts["vc_capable"], False)
        self.assertEqual(self.dev.facts["vc_mode"], None)
        self.assertEqual(self.dev.facts["vc_fabric"], None)
        self.assertEqual(self.dev.facts["vc_master"], None)

    @patch("jnpr.junos.Device.execute")
    @unittest.skipIf(sys.platform == "win32", "will work for windows in coming days")
    def test_vc_mmvcf(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_vc_mmvcf
        self.assertEqual(self.dev.facts["vc_capable"], True)
        self.assertEqual(self.dev.facts["vc_mode"], "Mixed")
        self.assertEqual(self.dev.facts["vc_fabric"], True)
        self.assertEqual(self.dev.facts["vc_master"], "0")

    @patch("jnpr.junos.Device.execute")
    @unittest.skipIf(sys.platform == "win32", "will work for windows in coming days")
    def test_vc_mmvc(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_vc_mmvc
        self.assertEqual(self.dev.facts["vc_capable"], True)
        self.assertEqual(self.dev.facts["vc_mode"], "Mixed")
        self.assertEqual(self.dev.facts["vc_fabric"], False)
        self.assertEqual(self.dev.facts["vc_master"], "0")

    def _read_file(self, fname):
        from ncclient.xml_ import NCElement

        fpath = os.path.join(os.path.dirname(__file__), "rpc-reply", fname)
        foo = open(fpath).read()

        rpc_reply = NCElement(
            foo, self.dev._conn._device_handler.transform_reply()
        )._NCElement__doc[0]
        return rpc_reply

    def _mock_manager_setup(self, *args, **kwargs):
        if kwargs:
            device_params = kwargs["device_params"]
            device_handler = make_device_handler(device_params)
            session = SSHSession(device_handler)
            return Manager(session, device_handler)

    def _mock_manager_vc(self, *args, **kwargs):
        if args:
            return self._read_file("vc_" + args[0].tag + ".xml")

    def _mock_manager_vc_dual_master(self, *args, **kwargs):
        if args:
            return self._read_file("vc_dual_master_" + args[0].tag + ".xml")

    def _mock_manager_vc_mmvcf(self, *args, **kwargs):
        if args:
            return self._read_file("vc_mmvcf_" + args[0].tag + ".xml")

    def _mock_manager_vc_mmvc(self, *args, **kwargs):
        if args:
            return self._read_file("vc_mmvc_" + args[0].tag + ".xml")

    def _mock_manager_vc_error(self, *args, **kwargs):
        if args:
            raise RpcError

    def _mock_manager_vc_empty(self, *args, **kwargs):
        if args:
            return True
