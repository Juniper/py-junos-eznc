__author__ = "Stacy Smith"
__credits__ = "Jeremy Schulman, Nitin Kumar"

import unittest
import nose2
from mock import patch, MagicMock
import os

from jnpr.junos import Device

from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession


class TestChassis(unittest.TestCase):
    @patch("ncclient.manager.connect")
    def setUp(self, mock_connect):
        mock_connect.side_effect = self._mock_manager_setup
        self.dev = Device(
            host="1.1.1.1", user="rick", password="password123", gather_facts=False
        )
        self.dev.open()

    @patch("jnpr.junos.Device.execute")
    def test_serialnumber_fact_from_chassis(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_chassis_serialnumber
        self.assertEqual(self.dev.facts["serialnumber"], "JN1249018AFB")
        self.assertFalse(self.dev.facts["RE_hw_mi"])

    @patch("jnpr.junos.Device.execute")
    def test_serialnumber_fact_from_backplane(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_backplane_serialnumber
        self.assertEqual(self.dev.facts["serialnumber"], "123456789")
        self.assertTrue(self.dev.facts["RE_hw_mi"])

    @patch("jnpr.junos.Device.execute")
    @patch("jnpr.junos.facts.get_chassis_inventory.ConnectNotMasterError")
    def test_serialnumber_not_master(self, mock_not_master, mock_execute):
        mock_execute.side_effect = self._mock_manager_connect_not_master
        self.assertEqual(self.dev.facts["serialnumber"], None)
        self.assertTrue(mock_not_master.called)

    @patch("jnpr.junos.Device.execute")
    @patch("jnpr.junos.facts.get_chassis_inventory.RpcError")
    def test_serialnumber_error_xml(self, mock_rpc_error, mock_execute):
        mock_execute.side_effect = self._mock_manager_error_xml
        self.assertEqual(self.dev.facts["serialnumber"], None)
        self.assertTrue(mock_rpc_error.called)

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

    def _mock_manager_chassis_serialnumber(self, *args, **kwargs):
        if args:
            return self._read_file("chassis_serialnumber_" + args[0].tag + ".xml")

    def _mock_manager_backplane_serialnumber(self, *args, **kwargs):
        if args:
            return self._read_file(
                "chassis_backplane_serialnumber_" + args[0].tag + ".xml"
            )

    def _mock_manager_connect_not_master(self, *args, **kwargs):
        if args:
            return self._read_file("chassis_connect_not_master_" + args[0].tag + ".xml")

    def _mock_manager_error_xml(self, *args, **kwargs):
        if args:
            return self._read_file("chassis_error_xml_" + args[0].tag + ".xml")
