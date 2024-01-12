__author__ = "Stacy Smith"
__credits__ = "Jeremy Schulman, Nitin Kumar"

import unittest
import nose2
from mock import patch, MagicMock
import os

from jnpr.junos import Device

from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession


class TestIriMapping(unittest.TestCase):
    @patch("ncclient.manager.connect")
    def setUp(self, mock_connect):
        mock_connect.side_effect = self._mock_manager_setup
        self.dev = Device(
            host="1.1.1.1", user="rick", password="password123", gather_facts=False
        )
        self.dev.open()

    @patch("jnpr.junos.Device.execute")
    def test_iri_host_to_ip_mapping_fact(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_current_re
        self.assertEqual(self.dev.facts["_iri_ip"]["re0"], ["128.0.0.4", "10.0.0.4"])

    @patch("jnpr.junos.Device.execute")
    def test_iri_ip_to_host_mapping_fact(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_current_re
        self.assertEqual(
            self.dev.facts["_iri_hostname"]["128.0.0.1"],
            ["master", "node", "fwdd", "member", "pfem"],
        )

    @patch("jnpr.junos.Device.execute")
    def test_iri_template_ip_to_host_mapping_fact(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_current_re
        self.assertEqual(
            self.dev.facts["_iri_hostname"]["190.0.1.1"], ["gnf1-master", "psd1-master"]
        )

    @patch("jnpr.junos.Device.execute")
    def test_iri_template_host_to_ip_mapping_fact(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_current_re
        self.assertEqual(
            self.dev.facts["_iri_ip"]["gnf1-master"], ["190.0.1.1", "190.1.1.1"]
        )

    @patch("jnpr.junos.Device.execute")
    def test_iri_template_host_to_ip_mapping_fact(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_current_re2
        self.assertEqual(self.dev.facts["_iri_ip"]["gnf1-master"], ["190.0.1.1"])

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

    def _mock_manager_current_re(self, *args, **kwargs):
        if args:
            return self._read_file("iri_mapping_" + args[0].tag + ".xml")

    def _mock_manager_current_re2(self, *args, **kwargs):
        if args:
            return self._read_file("iri_mapping2_" + args[0].tag + ".xml")
