__author__ = "Nitin Kumar, Rick Sherman"
__credits__ = "Jeremy Schulman"

import unittest
from nose.plugins.attrib import attr
from jnpr.junos.jxml import NAME, INSERT, remove_namespaces

@attr('unit')
class Test_JXML(unittest.TestCase):

    def test_name(self):
        op = NAME('test')
        self.assertEqual(op['name'], 'test')

    def test_insert(self):
        op = INSERT('test')
        self.assertEqual(op['insert'], 'test')

    def test_remove_namespaces(self):
        xmldata=\
        """<xsl:stylesheet xmlns:xsl="http://xml.juniper.net/junos">
                <xsl:template>
                    <xsl:attribute name="{myname}">
                    </xsl:attribute>
                </xsl:template>
            </xsl:stylesheet>"""
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xmldata)
        remove_namespaces(root)