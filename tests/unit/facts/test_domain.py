__author__ = "Nitin Kumar, Rick Sherman"
__credits__ = "Jeremy Schulman"

import unittest
from nose.plugins.attrib import attr
from mock import patch

from jnpr.junos.facts.domain import facts_domain
from jnpr.junos import Device


@attr('unit')
class TestDomain(unittest.TestCase):

    def setUp(self):
        self.dev = Device(host='1.1.1.1', user='rick', password='password123',
                          gather_facts=False)
        self.facts = {}

    @patch('jnpr.junos.facts.domain.FS.cat')
    def test_resolv_conf(self, mock_fs_cat):
        mock_fs_cat.return_value =\
            """# domain juniper.net
        search englab.juniper.net spglab.juniper.net juniper.net jnpr.net
        nameserver 10.11.12.13
        """
        self.facts['hostname'] = 'test'
        facts_domain(self.dev, self.facts)
        self.assertEqual(self.facts['domain'], 'juniper.net')
        self.assertEqual(self.facts['fqdn'], 'test.juniper.net')

    @patch('jnpr.junos.facts.domain.FS.cat')
    def test_resolv_conf_no_domain(self, mock_fs_cat):
        mock_fs_cat.return_value =\
            """
        search englab.juniper.net spglab.juniper.net juniper.net jnpr.net
        nameserver 10.11.12.13
        """
        self.facts['hostname'] = 'test'
        facts_domain(self.dev, self.facts)
        self.assertEqual(self.facts['domain'], None)
        self.assertEqual(self.facts['fqdn'], 'test')
