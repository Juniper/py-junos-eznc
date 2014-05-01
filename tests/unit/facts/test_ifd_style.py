__author__ = "Nitin Kumar, Rick Sherman"
__credits__ = "Jeremy Schulman"

import unittest
from nose.plugins.attrib import attr

from jnpr.junos import Device
from jnpr.junos.facts.ifd_style import facts_ifd_style as ifd_style


@attr('unit')
class TestIFDStyle(unittest.TestCase):

    def setUp(self):
        self.facts = {}
        self.dev = Device(host='1.1.1.1', user='rick', password='password123',
                          gather_facts=False)

    def test_ifd_style_if_condition(self):
        self.facts['personality'] = 'SWITCH'
        ifd_style(self.dev, self.facts)
        self.assertEqual(self.facts['ifd_style'], 'SWITCH')

    def test_ifd_style_else_condition(self):
        self.facts['personality'] = 'TEXT'
        ifd_style(self.dev, self.facts)
        self.assertEqual(self.facts['ifd_style'], 'CLASSIC')
