__author__ = "Stacy Smith"
__credits__ = "Jeremy Schulman, Nitin Kumar"

try:
    import unittest2 as unittest
except ImportError:
    import unittest
import nose2
import importlib
import sys

import jnpr.junos.facts


class TestFactInitialization(unittest.TestCase):
    def test_duplicate_facts(self):
        module = importlib.import_module("tests.unit.facts.dupe_foo1")
        sys.modules["jnpr.junos.facts.dupe_foo1"] = module
        module = importlib.import_module("tests.unit.facts.dupe_foo2")
        sys.modules["jnpr.junos.facts.dupe_foo2"] = module
        with self.assertRaises(RuntimeError):
            jnpr.junos.facts._build_fact_callbacks_and_doc_strings()
