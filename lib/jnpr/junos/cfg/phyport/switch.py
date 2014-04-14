# 3rd-party
from lxml.builder import E

# local
from jnpr.junos.cfg import Resource
from jnpr.junos import JXML
from jnpr.junos.cfg.phyport.base import PhyPortBase


class PhyPortSwitch(PhyPortBase):

    PORT_SPEED = {
        'auto': 'auto-negotiation',
        '10m': 'ethernet-10m',
        '100m': 'ethernet-100m',
        '1g': 'ethernet-1g'
    }

    # -----------------------------------------------------------------------
    # XML readers
    # -----------------------------------------------------------------------

    def _xml_to_py(self, has_xml, has_py):
        PhyPortBase._xml_to_py(self, has_xml, has_py)

        # speed, duplex, loopback are all under 'ether-options'
        ethopts = has_xml.find('ether-options')
        if ethopts is None:
            return

        if ethopts.find('loopback') is not None:
            has_py['loopback'] = True

        speed = ethopts.find('speed')
        if speed is not None:
            # take the first child element
            has_py['speed'] = speed[0].tag
            PhyPortBase._set_invert(has_py, 'speed', self.PORT_SPEED)

        Resource.copyifexists(ethopts, 'link-mode', has_py, 'duplex')
        if 'duplex' in has_py:
            PhyPortBase._set_invert(has_py, 'duplex', self.PORT_DUPLEX)

    # -----------------------------------------------------------------------
    # XML writers
    # -----------------------------------------------------------------------

    def _xml_hook_build_change_begin(self, xml):
        if any([this in self.should for this in ['speed', 'duplex',
                                                 'loopback']]):
            self._ethopts = E('ether-options')
            xml.append(self._ethopts)

    def _xml_change_speed(self, xml):
        speed_tag = self.PORT_SPEED.get(self.speed)
        add_this = E.speed(
            JXML.DEL) if speed_tag is None else E.speed(
            E(speed_tag))
        self._ethopts.append(add_this)
        return True

    def _xml_change_duplex(self, xml):
        value = self.PORT_DUPLEX.get(self.duplex)
        Resource.xml_set_or_delete(self._ethopts, 'link-mode', value)
        return True

    def _xml_change_loopback(self, xml):
        self._ethopts.append(
            Resource.xmltag_set_or_del(
                'loopback',
                self.loopback))
        return True
