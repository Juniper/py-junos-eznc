__author__ = "Nitin Kumar, Rick Sherman"
__credits__ = "Jeremy Schulman"

import unittest
from mock import patch
import nose2

from jnpr.junos import Device
from jnpr.junos.ofacts.personality import facts_personality as personality


class TestPersonality(unittest.TestCase):
    @patch("jnpr.junos.device.warnings")
    def setUp(self, mock_warnings):
        self.facts = {}
        self.dev = Device(
            host="1.1.1.1",
            user="rick",
            password="password123",
            gather_facts=False,
            fact_style="old",
        )

    def test_virtual_hassis(self):
        self.facts["model"] = "Virtual Chassis"
        self.facts["RE0"] = {"model": "QFX5100"}
        personality(self.dev, self.facts)
        self.assertEqual(self.facts["personality"], "SWITCH")

    def test_m_ex_qfx_series(self):
        self.facts["model"] = "QFX5100"
        personality(self.dev, self.facts)
        self.assertEqual(self.facts["personality"], "SWITCH")

    def test_mx_series(self):
        self.facts["model"] = "MX80"
        personality(self.dev, self.facts)
        self.assertEqual(self.facts["personality"], "MX")

    def test_vmx_series(self):
        self.facts["model"] = "vMX80"
        personality(self.dev, self.facts)
        self.assertEqual(self.facts["personality"], "MX")
        self.assertTrue(self.facts["virtual"])

    def test_vjx_series(self):
        self.facts["model"] = "VJX480"
        personality(self.dev, self.facts)
        self.assertEqual(self.facts["personality"], "SRX_BRANCH")
        self.assertTrue(self.facts["virtual"])

    def test_m_series(self):
        self.facts["model"] = "M7i"
        personality(self.dev, self.facts)
        self.assertEqual(self.facts["personality"], "M")

    def test_t_series(self):
        self.facts["model"] = "T320"
        personality(self.dev, self.facts)
        self.assertEqual(self.facts["personality"], "T")

    def test_ptx_series(self):
        self.facts["model"] = "PTX5000"
        personality(self.dev, self.facts)
        self.assertEqual(self.facts["personality"], "PTX")

    def test_srx_series(self):
        self.facts["model"] = "SRX210"
        personality(self.dev, self.facts)
        self.assertEqual(self.facts["personality"], "SRX_BRANCH")

    def test_srx_high_series(self):
        self.facts["model"] = "SRX5600"
        personality(self.dev, self.facts)
        self.assertEqual(self.facts["personality"], "SRX_HIGHEND")

    def test_personality_olive(self):
        self.facts["model"] = "olive"
        personality(self.dev, self.facts)
        self.assertEqual(self.facts["personality"], "OLIVE")

    def test_invalid_series(self):
        self.facts["model"] = "invalid"
        personality(self.dev, self.facts)
        self.assertEqual(self.facts["personality"], "UNKNOWN")
