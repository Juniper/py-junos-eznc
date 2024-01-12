# Tests in this file corresponds to /jnpr/junos/__init__.py

import unittest
import sys

import nose2
from mock import patch

__author__ = "Nitin Kumar"
__credits__ = "Jeremy Schulman"


class TestJunosInit(unittest.TestCase):
    def test_warning(self):
        print(sys.modules["sys"].version_info)
        with patch.object(sys.modules["sys"], "version_info", (3, 8, 0)) as mock_sys:
            from jnpr import junos

            self.assertEqual(mock_sys, (3, 8, 0))
