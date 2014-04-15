__author__ = "Nitin Kumar, Rick Sherman"
__credits__ = "Jeremy Schulman"

import unittest
from jnpr.junos import Device
from jnpr.junos.facts.personality import personality

facts={}
class TestPersonality(unittest.TestCase):

    def setUp(self):
        self.dev = Device(host='1.1.1.1', user='rick', password='password123',
                          gather_facts=False)

    def test_virtual_hassis(self):
        facts['model'] = 'Virtual Chassis'
        facts['RE0'] = {'model':'QFX5100'}
        personality(self.dev, facts)
        self.assertEqual(facts['personality'], 'SWITCH')


    def test_m_ex_qfx_series(self):
        facts['model'] = 'QFX5100'
        personality(self.dev, facts)
        self.assertEqual(facts['personality'], 'SWITCH')

    def test_mx_series(self):
        facts['model'] = 'MX80'
        personality(self.dev, facts)
        self.assertEqual(facts['personality'], 'MX')

    def test_vmx_series(self):
        facts['model'] = 'vMX80'
        personality(self.dev, facts)
        self.assertEqual(facts['personality'], 'MX')
        self.assertTrue(facts['virtual'])

    def test_vjx_series(self):
        facts['model'] = 'VJX480'
        personality(self.dev, facts)
        self.assertEqual(facts['personality'], 'SRX_BRANCH')
        self.assertTrue(facts['virtual'])

    def test_m_series(self):
        facts['model'] = 'M7i'
        personality(self.dev, facts)
        self.assertEqual(facts['personality'], 'M')

    def test_t_series(self):
        facts['model'] = 'T320'
        personality(self.dev, facts)
        self.assertEqual(facts['personality'], 'T')

    def test_ptx_series(self):
        facts['model'] = 'PTX5000'
        personality(self.dev, facts)
        self.assertEqual(facts['personality'], 'PTX')

    def test_srx_series(self):
        facts['model'] = 'SRX210'
        personality(self.dev, facts)
        self.assertEqual(facts['personality'], 'SRX_BRANCH')

    def test_srx_high_series(self):
        facts['model'] = 'SRX5600'
        personality(self.dev, facts)
        self.assertEqual(facts['personality'], 'SRX_HIGHEND')

    def test_invalid_series(self):
        facts['model'] = 'invalid'
        with self.assertRaises(RuntimeError):
            personality(self.dev, facts)

