__author__ = "Nitin Kumar, Rick Sherman"
__credits__ = "Jeremy Schulman"

import unittest
import nose2
from mock import patch, MagicMock
from lxml import etree

from jnpr.junos.ofacts.domain import facts_domain
from jnpr.junos import Device
from jnpr.junos.exception import RpcError


class TestDomain(unittest.TestCase):
    @patch("ncclient.manager.connect")
    @patch("jnpr.junos.device.warnings")
    def setUp(self, mock_warnings, mock_connect):
        self.dev = Device(
            host="1.1.1.1",
            user="rick",
            password="password123",
            gather_facts=False,
            fact_style="old",
        )
        self.dev.open()
        self.facts = {}

    @patch("jnpr.junos.ofacts.domain.FS.cat")
    def test_resolv_conf(self, mock_fs_cat):
        mock_fs_cat.return_value = """# domain juniper.net
        search englab.juniper.net spglab.juniper.net juniper.net jnpr.net
        nameserver 10.11.12.13
        """
        self.facts["hostname"] = "test"
        facts_domain(self.dev, self.facts)
        self.assertEqual(self.facts["domain"], "juniper.net")
        self.assertEqual(self.facts["fqdn"], "test.juniper.net")

    @patch("jnpr.junos.ofacts.domain.FS.cat")
    def test_resolv_conf_no_domain(self, mock_fs_cat):
        mock_fs_cat.return_value = """
        search englab.juniper.net spglab.juniper.net juniper.net jnpr.net
        nameserver 10.11.12.13
        """
        self.facts["hostname"] = "test"
        facts_domain(self.dev, self.facts)
        self.assertEqual(self.facts["domain"], None)
        self.assertEqual(self.facts["fqdn"], "test")

    @patch("jnpr.junos.ofacts.domain.FS.cat")
    def test_resolv_conf_file_absent_under_etc(self, mock_fs_cat):
        mock_fs_cat.side_effect = [None, "domain juniper.net"]
        self.facts["hostname"] = "test"
        facts_domain(self.dev, self.facts)
        self.assertEqual(self.facts["domain"], "juniper.net")
        self.assertEqual(self.facts["fqdn"], "test.juniper.net")

    def test_domain_in_configuration(self):
        xmldata = etree.XML(
            """<configuration><system>
                <domain-name>testing.net</domain-name>
                </system></configuration>"""
        )
        self.dev.rpc.get_config = MagicMock(side_effect=xmldata)
        self.facts["hostname"] = "test"
        facts_domain(self.dev, self.facts)
        self.assertEqual(self.facts["domain"], "testing.net")
        self.assertEqual(self.facts["fqdn"], "test.testing.net")

    @patch("jnpr.junos.ofacts.domain.FS.cat")
    def test_domain_rpc_error(self, mock_fs_cat):
        self.dev.rpc.get_config = MagicMock(side_effect=RpcError)
        mock_fs_cat.return_value = """# domain juniper.net
        search englab.juniper.net spglab.juniper.net juniper.net jnpr.net
        nameserver 10.11.12.13
        """
        self.facts["hostname"] = "test"
        facts_domain(self.dev, self.facts)
        self.assertEqual(self.facts["domain"], "juniper.net")
        self.assertEqual(self.facts["fqdn"], "test.juniper.net")
