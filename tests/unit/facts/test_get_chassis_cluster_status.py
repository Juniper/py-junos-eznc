__author__ = "Stacy Smith"
__credits__ = "Jeremy Schulman, Nitin Kumar"

import unittest
import nose2
from mock import patch, MagicMock
import os
from lxml import etree

from jnpr.junos import Device
from jnpr.junos.exception import RpcError

from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession


class TestGetChassisClusterStatus(unittest.TestCase):
    @patch("ncclient.manager.connect")
    def setUp(self, mock_connect):
        mock_connect.side_effect = self._mock_manager_setup
        self.dev = Device(
            host="1.1.1.1", user="rick", password="password123", gather_facts=False
        )
        self.dev.open()

    @patch("jnpr.junos.Device.execute")
    def test_srx_cluster_fact_none(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_rpc_error
        self.assertEqual(self.dev.facts["srx_cluster"], None)

    @patch("jnpr.junos.Device.execute")
    def test_srx_cluster_fact_false(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_false
        self.assertEqual(self.dev.facts["srx_cluster"], False)

    @patch("jnpr.junos.Device.execute")
    def test_srx_cluster_fact_true(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_true
        self.assertEqual(self.dev.facts["srx_cluster"], True)

    @patch("jnpr.junos.Device.execute")
    def test_srx_cluster_id_fact(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_true
        self.assertEqual(self.dev.facts["srx_cluster_id"], "1")

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

    def _mock_manager_rpc_error(self, *args, **kwargs):
        if args:
            raise RpcError()

    def _mock_manager_false(self, *args, **kwargs):
        if args:
            return self._read_file("cluster_false_" + args[0].tag + ".xml")

    def _mock_manager_true(self, *args, **kwargs):
        if args:
            return self._read_file("cluster_true_" + args[0].tag + ".xml")
