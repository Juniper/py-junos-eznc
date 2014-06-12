__author__ = "Rick Sherman"
__credits__ = "Jeremy Schulman"

import unittest
from nose.plugins.attrib import attr

from jnpr.junos.factory.viewfields import ViewFields


@attr('unit')
class TestFactoryViewFields(unittest.TestCase):

    def setUp(self):
        self.vf = ViewFields()

    def test_viewfields_string(self):
        self.vf.str('test', key='123')
        self.assertEqual(self.vf.end['test']['key'], '123')

    def test_viewfields_astype(self):
        self.vf.astype('test', astype=1)
        self.assertEqual(self.vf.end['test']['astype'], 1)

    def test_viewfields_int(self):
        self.vf.int('test')
        self.assertEqual(self.vf.end['test']['astype'], int)

    def test_viewfields_flag(self):
        self.vf.flag('test')
        self.assertEqual(self.vf.end['test']['astype'], bool)

    def test_viewfields_table(self):
        self.vf.table('test', [])
        self.assertEqual(self.vf.end['test']['table'], [])
