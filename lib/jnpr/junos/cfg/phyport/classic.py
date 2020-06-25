# 3rd-party
from lxml.builder import E

# local
from jnpr.junos.cfg.resource import Resource
from jnpr.junos import JXML
from jnpr.junos.cfg.phyport.base import PhyPortBase


class PhyPortClassic(PhyPortBase):

    # -----------------------------------------------------------------------
    # XML readers
    # -----------------------------------------------------------------------

    def _xml_to_py(self, has_xml, has_py):
        PhyPortBase._xml_to_py(self, has_xml, has_py)

        Resource.copyifexists(has_xml, "speed", has_py)
        Resource.copyifexists(has_xml, "link-mode", has_py, "duplex")
        if has_xml.find("gigether-options/loopback") is not None:
            has_py["loopback"] = True
        has_py["$unit_count"] = len(has_xml.findall("unit"))

        # normalizers
        if "duplex" in has_py:
            PhyPortBase._set_invert(has_py, "duplex", self.PORT_DUPLEX)

    # -----------------------------------------------------------------------
    # XML writers
    # -----------------------------------------------------------------------

    def _xml_change_speed(self, xml):
        Resource.xml_set_or_delete(xml, "speed", self.speed)
        return True

    def _xml_change_duplex(self, xml):
        value = self.PORT_DUPLEX.get(self.duplex)
        Resource.xml_set_or_delete(xml, "link-mode", value)
        return True

    def _xml_change_loopback(self, xml):
        opts = E("gigether-options")
        opts.append(Resource.xmltag_set_or_del("loopback", self.loopback))
        xml.append(opts)
        return True
