__author__ = "Stacy Smith"
__credits__ = "Jeremy Schulman, Nitin Kumar"

import unittest
import nose2
from mock import patch, MagicMock
import os
from lxml import etree

from jnpr.junos import Device
from jnpr.junos.exception import PermissionError

from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession


class TestDomain(unittest.TestCase):
    @patch("ncclient.manager.connect")
    def setUp(self, mock_connect):
        mock_connect.side_effect = self._mock_manager_setup
        self.dev = Device(
            host="1.1.1.1", user="rick", password="password123", gather_facts=False
        )
        self.dev.open()

    @patch("jnpr.junos.Device.execute")
    def test_domain_fact_from_config(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_domain_config
        self.assertEqual(self.dev.facts["domain"], "juniper.net")
        self.assertEqual(self.dev.facts["fqdn"], "r0.juniper.net")

    @patch("jnpr.junos.Device.execute")
    def test_domain_fact_from_file(self, mock_execute):
        self.dev.facts._cache["hostname"] = "r0"
        mock_execute.side_effect = self._mock_manager_domain_file
        self.assertEqual(self.dev.facts["domain"], "juniper.net")
        self.assertEqual(self.dev.facts["fqdn"], "r0.juniper.net")

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

    def _mock_manager_domain_config(self, *args, **kwargs):
        if args:
            return self._read_file("domain_config_" + args[0].tag + ".xml")

    def _mock_manager_domain_file(self, *args, **kwargs):
        if args:
            if args[0].tag == "get-configuration":
                xml = """
                    <rpc-error>
                        <error-type>protocol</error-type>
                        <error-tag>operation-failed</error-tag>
                        <error-severity>error</error-severity>
                        <error-message>permission denied</error-message>
                        <error-info>
                            <bad-element>system</bad-element>
                        </error-info>
                    </rpc-error>
                """
                rsp = etree.XML(xml)
                raise PermissionError(rsp=rsp)
            else:
                return self._read_file("domain_file_" + args[0].tag + ".xml")
