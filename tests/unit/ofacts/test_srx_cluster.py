__author__ = "Nitin Kumar, Rick Sherman"
__credits__ = "Jeremy Schulman"

import unittest
import nose2
from mock import patch
import os

from jnpr.junos import Device
from jnpr.junos.ofacts.srx_cluster import facts_srx_cluster as srx_cluster

from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession


class TestSrxCluster(unittest.TestCase):
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
    def test_srx_cluster(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.facts["personality"] = "SRX"
        self.facts["master"] = ["RE0"]
        srx_cluster(self.dev, self.facts)
        self.assertTrue(self.facts["srx_cluster"])

    @patch("jnpr.junos.device.warnings")
    def test_srx_cluster_none(self, mock_warnings):
        self.facts["personality"] = "MX"
        self.assertEqual(srx_cluster(self.dev, self.facts), None)

    @patch("jnpr.junos.Device.execute")
    def test_srx_cluster_no_node(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.facts["personality"] = "SRX"
        srx_cluster(self.dev, self.facts)
        self.assertTrue(self.facts["srx_cluster"])

    @patch("jnpr.junos.Device.execute")
    def test_srx_cluster_node(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.facts["personality"] = "SRX"
        self.facts["master"] = ["RE1"]
        srx_cluster(self.dev, self.facts)
        self.assertTrue(self.facts["srx_cluster"])

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
            return self._read_file(args[0].tag + ".xml")
