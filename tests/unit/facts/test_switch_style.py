__author__ = "Nitin Kumar, Rick Sherman"
__credits__ = "Jeremy Schulman"

import unittest
from jnpr.junos import Device
from jnpr.junos.facts.switch_style import switch_style

facts={}
class TestSwitchStyle(unittest.TestCase):

    def setUp(self):
        self.dev = Device(host='1.1.1.1', user='rick', password='password123',
                          gather_facts=False)

    def test_switch_style_mx_srx(self):
        facts['personality'] = 'SRX_HIGHEND'
        switch_style(self.dev, facts)
        self.assertEqual(facts['switch_style'], 'BRIDGE_DOMAIN')

    def test_switch_style_model_firefly(self):
        facts['personality'] = 'SWITCH'
        facts['model'] = 'FIReFly'
        switch_style(self.dev, facts)
        self.assertEqual(facts['switch_style'], 'NONE')

    def test_switch_style_model_ex9000(self):
        facts['personality'] = 'SWITCH'
        facts['model'] = 'EX9000'
        switch_style(self.dev, facts)
        self.assertEqual(facts['switch_style'], 'VLAN_L2NG')

    def test_switch_style_model_not_specific(self):
        facts['personality'] = 'SWITCH'
        facts['model'] = 'abc'
        switch_style(self.dev, facts)
        self.assertEqual(facts['switch_style'], 'VLAN')

    def test_switch_style_persona_not_specific(self):
        facts['personality'] = 'PTX'
        facts['model'] = 'abc'
        switch_style(self.dev, facts)
        self.assertEqual(facts['switch_style'], 'NONE')

