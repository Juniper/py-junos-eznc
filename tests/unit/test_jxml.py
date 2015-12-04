__author__ = "Nitin Kumar, Rick Sherman"
__credits__ = "Jeremy Schulman"

import os
import unittest
from io import StringIO
from nose.plugins.attrib import attr
from mock import patch
from jnpr.junos.jxml import NAME, INSERT, remove_namespaces, cscript_conf
from lxml import etree


@attr('unit')
class Test_JXML(unittest.TestCase):

    def test_name(self):
        op = NAME('test')
        self.assertEqual(op['name'], 'test')

    def test_insert(self):
        op = INSERT('test')
        self.assertEqual(op['insert'], 'test')

    def test_remove_namespaces(self):
        xmldata = \
            u"""<xsl:stylesheet xmlns:xsl="http://xml.juniper.net/junos">
                    <xsl:template>
                        <!-- Handle comments properly -->
                        <xsl:attribute name="{myname}">
                        </xsl:attribute>
                    </xsl:template>
                </xsl:stylesheet>"""
        import xml.etree.ElementTree as ET
        parser = ET.XMLParser()
        root   = ET.parse(StringIO(xmldata), parser)
        test = remove_namespaces(root)
        for elem in test.getiterator():
            i = elem.tag.find('}')
            if i > 0:
                i = i + 1
        self.assertTrue(i <= 0)

    def test_cscript_conf(self):
        op = cscript_conf(self._read_file('get-configuration.xml'))
        self.assertTrue(isinstance(op, etree._Element))

    @patch('ncclient.manager.make_device_handler')
    def test_cscript_conf_return_none(self, dev_handler):
        dev_handler.side_effects = ValueError
        op = cscript_conf(self._read_file('get-configuration.xml'))
        self.assertTrue(op is None)

    def _read_file(self, fname):
        fpath = os.path.join(os.path.dirname(__file__),
                             'rpc-reply', fname)
        foo = etree.fromstring(open(fpath).read())
        return foo

