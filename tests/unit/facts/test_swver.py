__author__ = "Stacy Smith"
__credits__ = "Jeremy Schulman, Nitin Kumar"

import six

try:
    import unittest2 as unittest
except:
    import unittest
import nose2

from jnpr.junos.facts.swver import version_info, get_facts


class TestVersionInfo(unittest.TestCase):
    if six.PY2:
        assertCountEqual = unittest.TestCase.assertItemsEqual

    def test_version_info_after_type_len_else(self):
        self.assertEqual(version_info("12.1X46-D10").build, None)

    def test_version_info_X_type_non_hyphenated(self):
        self.assertCountEqual(
            version_info("11.4X12.2"),
            [("build", 2), ("major", (11, 4)), ("minor", "12"), ("type", "X")],
        )

    def test_version_info_X_type_non_hyphenated_nobuild(self):
        self.assertCountEqual(
            version_info("11.4X12"),
            [("build", None), ("major", (11, 4)), ("minor", "12"), ("type", "X")],
        )

    def test_version_info_constructor_else_exception(self):
        self.assertEqual(version_info("11.4R7").build, "7")

    def test_version_info_repr(self):
        self.assertEqual(
            repr(version_info("11.4R7.5")),
            "junos.version_info(major=(11, 4), " "type=R, minor=7, build=5)",
        )

    def test_version_info_lt(self):
        self.assertTrue(version_info("13.3-20131120") < (14, 1))

    def test_version_info_lt_eq(self):
        self.assertTrue(version_info("13.3-20131120") <= (14, 1))

    def test_version_info_gt(self):
        self.assertTrue(version_info("13.3-20131120") > (12, 1))

    def test_version_info_gt_eq(self):
        self.assertTrue(version_info("13.3-20131120") >= (12, 1))

    def test_version_info_eq(self):
        self.assertTrue(version_info("13.3-20131120") == (13, 3))

    def test_version_info_not_eq(self):
        self.assertTrue(version_info("13.3-20131120") != (15, 3))

    def test_version_to_json(self):
        import json

        self.assertEqual(
            eval(json.dumps(version_info("11.4R7.5"))),
            {"major": [11, 4], "type": "R", "build": 5, "minor": "7"},
        )

    def test_version_to_yaml(self):
        import yaml

        self.assertEqual(
            yaml.dump(version_info("11.4R7.5")),
            "build: 5\nmajor: !!python/tuple\n- 11\n- 4\nminor: '7'\ntype: R\n",
        )

    def test_version_iter(self):
        self.assertCountEqual(
            version_info("11.4R7.5"),
            [("build", 5), ("major", (11, 4)), ("minor", "7"), ("type", "R")],
        )

    def test_version_feature_velocity(self):
        self.assertCountEqual(
            version_info("15.4F7.5"),
            [("build", 5), ("major", (15, 4)), ("minor", "7"), ("type", "F")],
        )

    def test_emptyget_facts(self):
        self.assertEqual(get_facts(None), {})
