__author__ = "Nitin Kumar, Rick Sherman"
__credits__ = "Jeremy Schulman"

import unittest
from jnpr.junos import Device
from jnpr.junos.facts.ifd_style import ifd_style

facts={}
class TestIFDStyle(unittest.TestCase):

    def setUp(self):
        self.dev = Device(host='1.1.1.1', user='rick', password='password123',
                          gather_facts=False)

    def test_ifd_style_if_condition(self):
        facts['personality'] = 'SWITCH'
        ifd_style(self.dev, facts)
        self.assertEqual(facts['ifd_style'], 'SWITCH')

    def test_ifd_style_else_condition(self):
        facts['personality'] = 'TEXT'
        ifd_style(self.dev, facts)
        self.assertEqual(facts['ifd_style'], 'CLASSIC')

