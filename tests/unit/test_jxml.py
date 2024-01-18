import os
import unittest
from io import StringIO
import nose2
from mock import patch
from jnpr.junos.jxml import (
    NAME,
    INSERT,
    remove_namespaces,
    cscript_conf,
    normalize_xslt,
)
from lxml import etree
from ncclient.xml_ import NCElement

__author__ = "Nitin Kumar, Rick Sherman"
__credits__ = "Jeremy Schulman"


class Test_JXML(unittest.TestCase):
    def test_name(self):
        op = NAME("test")
        self.assertEqual(op["name"], "test")

    def test_insert(self):
        op = INSERT("test")
        self.assertEqual(op["insert"], "test")

    def test_remove_namespaces(self):
        xmldata = """<xsl:stylesheet xmlns:xsl="http://xml.juniper.net/junos">
                    <xsl:template>
                        <!-- Handle comments properly -->
                        <xsl:attribute name="{myname}">
                        </xsl:attribute>
                    </xsl:template>
                </xsl:stylesheet>"""
        import xml.etree.ElementTree as ET

        parser = ET.XMLParser()
        root = ET.parse(StringIO(xmldata), parser)
        test = remove_namespaces(root)
        for elem in test.iter():
            i = elem.tag.find("}")
            if i > 0:
                i = i + 1
        self.assertTrue(i <= 0)

    def test_cscript_conf(self):
        op = cscript_conf(self._read_file("get-configuration.xml"))
        self.assertTrue(isinstance(op, etree._Element))

    @patch("ncclient.manager.make_device_handler")
    def test_cscript_conf_return_none(self, dev_handler):
        dev_handler.side_effects = ValueError
        op = cscript_conf(self._read_file("get-configuration.xml"))
        self.assertTrue(op is None)

    def test_cscript_conf_output_tag_child_element(self):
        xmldata = """<rpc-reply message-id="urn:uuid:932d11dc-9ae5-4d25-81fa-8b50ea2d3a03" xmlns:junos="http://xml.juniper.net/junos/19.3R0/junos">
  <output>
    shutdown: [pid 8683]
    Shutdown NOW!
  </output>
</rpc-reply>
"""
        xmldata_without_ns = """<rpc-reply message-id="urn:uuid:932d11dc-9ae5-4d25-81fa-8b50ea2d3a03">
  <output>
    shutdown: [pid 8683]
    Shutdown NOW!
  </output>
</rpc-reply>
"""
        rpc_reply = NCElement(xmldata, normalize_xslt.encode("UTF-8"))
        self.assertEqual(str(rpc_reply), xmldata_without_ns)

    def test_cscript_conf_output_tag_not_first_child_element(self):
        xmldata = """<rpc-reply message-id="urn:uuid:932d11dc-9ae5-4d25-81fa-8b50ea2d3a03" xmlns:junos="http://xml.juniper.net/junos/19.3R0/junos">
  <xyz>
    <output>
      shutdown: [pid 8683]
      Shutdown NOW!
    </output>
  </xyz>
</rpc-reply>
"""
        xmldata_without_ns = """<rpc-reply message-id="urn:uuid:932d11dc-9ae5-4d25-81fa-8b50ea2d3a03">
  <xyz>
    <output>shutdown: [pid 8683] Shutdown NOW!</output>
  </xyz>
</rpc-reply>
"""
        rpc_reply = NCElement(xmldata, normalize_xslt.encode("UTF-8"))
        self.assertEqual(str(rpc_reply), xmldata_without_ns)

    def _read_file(self, fname):
        fpath = os.path.join(os.path.dirname(__file__), "rpc-reply", fname)
        with open(fpath) as fp:
            foo = fp.read()
        return foo
