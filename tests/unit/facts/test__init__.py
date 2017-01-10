__author__ = "Stacy Smith"
__credits__ = "Jeremy Schulman, Nitin Kumar"

import unittest2 as unittest
from nose.plugins.attrib import attr
from mock import patch, MagicMock
import importlib

import jnpr.junos.facts

@attr('unit')
class TestFactInitialization(unittest.TestCase):

    @patch('jnpr.junos.facts._import_fact_modules')
    def test_duplicate_facts(self, mock_import):
        mock_import.side_effect = self._mock_import_side_effect
        with self.assertRaises(RuntimeError):
            jnpr.junos.facts._build_fact_callbacks_and_doc_strings()

    def _mock_import_side_effect(self, *args, **kwargs):
        modules = []
        modules.append(importlib.import_module('tests.unit.facts.dupe_foo1'))
        modules.append(importlib.import_module('tests.unit.facts.dupe_foo2'))
        return modules
