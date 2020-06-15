# 3rd-party
from lxml.builder import E

# local module
from jnpr.junos.cfg.resource import Resource


class PhyPortBase(Resource):

    """
    [edit interfaces <name>]

    Resource name: str
      <name> is the interface-name (IFD), e.g. 'ge-0/0/0'
    """

    PROPERTIES = [
        "admin",  # True
        "description",  # str
        "speed",  # ['10m','100m','1g','10g']
        "duplex",  # ['full','half']
        "mtu",  # int
        "loopback",  # True
        "$unit_count",  # number of units defined
    ]

    PORT_DUPLEX = {"full": "full-duplex", "half": "half-duplex"}

    @classmethod
    def _set_invert(cls, in_this, item, from_this):
        from_item = in_this[item]
        in_this[item] = [_k for _k, _v in from_this.items() if _v == from_item][0]

    # -----------------------------------------------------------------------
    # XML readers
    # -----------------------------------------------------------------------

    def _xml_at_top(self):
        return E.interfaces(E.interface(E.name(self._name)))

    def _xml_at_res(self, xml):
        return xml.find(".//interface")

    def _xml_to_py(self, has_xml, has_py):
        # common to all subclasses
        Resource._r_has_xml_status(has_xml, has_py)
        has_py["admin"] = bool(has_xml.find("disable") is None)
        Resource.copyifexists(has_xml, "description", has_py)
        Resource.copyifexists(has_xml, "mtu", has_py)
        has_py["$unit_count"] = len(has_xml.findall("unit"))

    # -----------------------------------------------------------------------
    # XML writers
    # -----------------------------------------------------------------------

    # description handed by Resource

    def _xml_change_admin(self, xml):
        xml.append(Resource.xmltag_set_or_del("disable", (self.admin is False)))
        return True

    def _xml_change_mtu(self, xml):
        Resource.xml_set_or_delete(xml, "mtu", self.mtu)
        return True

    # -----------------------------------------------------------------------
    # Manager List, Catalog
    # -----------------------------------------------------------------------

    def _r_list(self):
        got = self.R.get_interface_information(
            media=True, interface_name="[efgx][et]-*"
        )
        self._rlist = [
            name.text.strip() for name in got.xpath("physical-interface/name")
        ]
