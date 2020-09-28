from ncclient import manager
from ncclient.xml_ import NCElement
from lxml import etree
import six

"""
  These are Junos XML 'helper' definitions use for generic XML processing

  .DEL to delete an item
  .REN to rename an item, requires the use of NAME()

  .INSERT(<'before'|'after'>) to reorder an item, requires the use of NAME()
  .BEFORE to reorder an item before another, requires the use of NAME()
  .AFTER to reorder an item after another, requires the use of NAME()

  .NAME(name) to assign the name attribute

"""

DEL = {"delete": "delete"}  # Junos XML resource delete
REN = {"rename": "rename"}  # Junos XML resource rename
ACTIVATE = {"active": "active"}  # activate resource
DEACTIVATE = {"inactive": "inactive"}  # deactivate resource
REPLACE = {"replace": "replace"}  # replace elements


def NAME(name):
    return {"name": name}


def INSERT(cmd):
    return {"insert": cmd}


BEFORE = {"insert": "before"}
AFTER = {"insert": "after"}

# used with <get-configuration> to load only the object identifiers and
# not all the subsequent configuration

NAMES_ONLY = {"recurse": "false"}

# for <get-configuration>, attributes to retrieve from apply-groups
INHERIT = {"inherit": "inherit"}
INHERIT_GROUPS = {"inherit": "inherit", "groups": "groups"}
INHERIT_DEFAULTS = {"inherit": "defaults", "groups": "groups"}

# XSLT for on-box commit script
conf_xslt = """\
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
    <xsl:output method="xml" indent="yes"/>
    <xsl:strip-space elements="*"/>

    <xsl:param name="subSelectionXPath" />

    <xsl:template match="/">
        <xsl:apply-templates
            select="$subSelectionXPath/ancestor::*[position()=last()]"/>
    </xsl:template>

    <xsl:template match="*">
        <xsl:choose>

            <xsl:when test="$subSelectionXPath/ancestor::*
                [generate-id() = generate-id(current())]">
                <xsl:copy>
                    <xsl:copy-of select="@*"/>

                    <xsl:choose>
                        <xsl:when test="generate-id(.)=
                            generate-id($subSelectionXPath/ancestor::*[1])">
                            <xsl:copy-of select="$subSelectionXPath"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:apply-templates select="*"/>
                        </xsl:otherwise>
                    </xsl:choose>

                </xsl:copy>
            </xsl:when>
            <xsl:otherwise/>
        </xsl:choose>
    </xsl:template>
</xsl:stylesheet>"""

conf_xslt_root = etree.XML(conf_xslt)
conf_transform = etree.XSLT(conf_xslt_root)


normalize_xslt = """\
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="xml" indent="no"/>

    <xsl:template match="/*[local-name()='rpc-reply']/*[local-name()='output']">
        <output>
        <xsl:value-of select="."/>
        </output>
    </xsl:template>

    <xsl:template match="/|comment()|processing-instruction()">
        <xsl:copy>
            <xsl:apply-templates/>
        </xsl:copy>
    </xsl:template>

    <xsl:template match="*">
        <xsl:element name="{local-name()}">
            <xsl:apply-templates select="@*|node()"/>
        </xsl:element>
    </xsl:template>

    <xsl:template match="@*">
        <xsl:attribute name="{local-name()}">
            <xsl:value-of select="."/>
        </xsl:attribute>
    </xsl:template>

    <xsl:template match="text()">
        <xsl:value-of select="normalize-space(.)"/>
    </xsl:template>
</xsl:stylesheet>"""


# XSLT to strip comments
strip_comments_xslt = """\
<xsl:stylesheet version="1.0"
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output omit-xml-declaration="yes" indent="yes"/>
  <xsl:strip-space elements="*"/>

  <xsl:template match="node()|@*" name="identity">
        <xsl:copy>
            <xsl:apply-templates select="node()|@*"/>
        </xsl:copy>
   </xsl:template>
   <xsl:template match="comment()"/>
</xsl:stylesheet>"""

strip_xslt_root = etree.XML(strip_comments_xslt)
strip_comments_transform = etree.XSLT(strip_xslt_root)

# XSLT to strip <rpc-error> elements
strip_rpc_error_xslt = """
<xsl:stylesheet version="1.0"
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output omit-xml-declaration="yes" indent="yes"/>
  <xsl:strip-space elements="*"/>

    <xsl:template match="node()|@*">
      <xsl:copy>
         <xsl:apply-templates select="node()|@*"/>
      </xsl:copy>
    </xsl:template>

    <xsl:template match="rpc-error"/>
</xsl:stylesheet>
"""

strip_rpc_error_root = etree.XML(strip_rpc_error_xslt)
strip_rpc_error_transform = etree.XSLT(strip_rpc_error_root)


def remove_namespaces(xml):
    for elem in xml.getiterator():
        if elem.tag is etree.Comment:
            continue
        i = elem.tag.find("}")
        if i > 0:
            elem.tag = elem.tag[i + 1 :]
    return xml


def remove_namespaces_and_spaces(xml):
    for elem in xml.getiterator():
        if elem.tag is etree.Comment:
            continue
        # Remove namespace from attributes
        for k, v in elem.attrib.items():
            i = k.find("}")
            if i >= 0:
                del elem.attrib[k]
                k = k[i + 1 :]
                elem.set(k, v)
        # Remove namespace from tags
        i = elem.tag.find("}")
        if i >= 0:
            elem.tag = elem.tag[i + 1 :]
        # remove white spaces from text
        if elem.text:
            elem.text = elem.text.strip()
    return xml


def rpc_error(rpc_xml):
    """
    extract the various bits from an <rpc-error> element
    into a dictionary
    """
    remove_namespaces(rpc_xml)

    if "rpc-reply" == rpc_xml.tag:
        rpc_xml = rpc_xml[0]

    def find_strip(x):
        ele = rpc_xml.find(x)
        return ele.text.strip() if ele is not None and ele.text is not None else None

    this_err = {}
    this_err["severity"] = find_strip("error-severity")
    this_err["source"] = find_strip("source-daemon")
    this_err["edit_path"] = find_strip("error-path")
    this_err["bad_element"] = find_strip("error-info/bad-element")
    this_err["message"] = find_strip("error-message")

    return this_err


def cscript_conf(reply):
    try:
        device_params = {"name": "junos"}
        device_handler = manager.make_device_handler(device_params)
        transform_reply = device_handler.transform_reply()
        return NCElement(reply, transform_reply)._NCElement__doc
    except:
        return None


# xslt to remove prefix like junos:ns
strip_namespaces_prefix = six.b(
    """<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xml" indent="no" omit-xml-declaration="no" />

    <xsl:template match="/ |comment() |processing-instruction()">
        <xsl:copy>
          <xsl:apply-templates select="/*" />
        </xsl:copy>
    </xsl:template>

    <xsl:template match="*">
        <xsl:element name="{local-name()}" namespace="{namespace-uri()}">
          <xsl:apply-templates select="@*|node()" />
        </xsl:element>
    </xsl:template>

    <xsl:template match="@*">
        <xsl:attribute name="{local-name()}">
          <xsl:value-of select="." />
        </xsl:attribute>
    </xsl:template>
</xsl:stylesheet>"""
)
