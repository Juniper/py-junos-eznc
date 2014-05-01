__author__ = "Nitin Kumar, Rick Sherman"
__credits__ = "Jeremy Schulman"

import unittest
from nose.plugins.attrib import attr

from jnpr.junos import Device
from jnpr.junos.facts.switch_style import facts_switch_style as switch_style


@attr('unit')
class TestSwitchStyle(unittest.TestCase):

    def setUp(self):
        self.facts = {}
        self.dev = Device(host='1.1.1.1', user='rick', password='password123',
                          gather_facts=False)

    def test_switch_style_mx_srx(self):
        self.facts['personality'] = 'SRX_HIGHEND'
        switch_style(self.dev, self.facts)
        self.assertEqual(self.facts['switch_style'], 'BRIDGE_DOMAIN')

    def test_switch_style_model_firefly(self):
        self.facts['personality'] = 'SWITCH'
        self.facts['model'] = 'FIReFly'
        switch_style(self.dev, self.facts)
        self.assertEqual(self.facts['switch_style'], 'NONE')

    def test_switch_style_model_ex9000(self):
        self.facts['personality'] = 'SWITCH'
        self.facts['model'] = 'EX9000'
        switch_style(self.dev, self.facts)
        self.assertEqual(self.facts['switch_style'], 'VLAN_L2NG')

    def test_switch_style_model_not_specific(self):
        self.facts['personality'] = 'SWITCH'
        self.facts['model'] = 'abc'
        switch_style(self.dev, self.facts)
        self.assertEqual(self.facts['switch_style'], 'VLAN')

    def test_switch_style_persona_not_specific(self):
        self.facts['personality'] = 'PTX'
        self.facts['model'] = 'abc'
        switch_style(self.dev, self.facts)
        self.assertEqual(self.facts['switch_style'], 'NONE')
