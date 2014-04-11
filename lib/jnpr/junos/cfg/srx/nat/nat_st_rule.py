# 3rd-party modules
from lxml.builder import E

# module packages
from jnpr.junos.cfg import Resource
from jnpr.junos import jxml as JXML
from jnpr.junos.cfg.srx.nat.nat_proxy_arp import NatProxyArp


class NatStaticRule(Resource):

    """
    [edit security nat static rule-set <ruleset_name> rule <rule_name>]

    Resource namevar:
      rule_name, string. The ruleset_name is obtained from the resource parent

    """

    PROPERTIES = [
        "description",
        "match_dst_addr",
        "match_dst_port",
        "nat_addr",
        "nat_port",
        "proxy_interface"
    ]

    # -----------------------------------------------------------------------
    # XML read
    # -----------------------------------------------------------------------

    def _xml_at_top(self):
        return E.security(E.nat(E.static(
            E('rule-set',
              E.name(self.P._name),
              E.rule(E.name(self._name))
              )
        )))

    def _xml_at_res(self, xml):
        return xml.find('.//rule')

    def _xml_to_py(self, as_xml, to_py):
        """
        converts Junos XML to native Python
        """
        Resource._r_has_xml_status(as_xml, to_py)
        Resource.copyifexists(as_xml, 'description', to_py)
        e = as_xml.find('static-nat-rule-match')
        to_py['match_dst_addr'] = e.find('destination-address').text

    # -----------------------------------------------------------------------
    # XML write
    # -----------------------------------------------------------------------

    def _xml_hook_build_change_begin(self, xml):
        if 'nat_port' not in self.should:
            # if 'nat_port' is not provided, then default to the
            # 'match_dst_port' value
            self.should['nat_port'] = self['match_dst_port']

        if 'match_dst_addr' in self.should and 'proxy_interface' in self.has:
            # if we are changing the 'match_dst_addr' and we also have a proxy
            # interface, then we need to update the proxy_interface value to
            # the new match_dst_addr value. start by deleting the existing one:
            namevar = (self['proxy_interface'], self.has['match_dst_addr'])
            NatProxyArp(self._junos, namevar).delete()

            if 'proxy_interface' not in self.should:
                # if the 'proxy_interface' value was not actually changed, then
                # simply copy the current one into :should:  this will trigger
                # the flush/create in the property-writer below
                self.should['proxy_interface'] = self.has['proxy_interface']

        # build up some XML that will be used by the property-writers
        match = E('static-nat-rule-match')
        xml.append(match)
        then = E.then(E('static-nat', E('prefix')))
        xml.append(then)
        self._rxml_match = match
        self._rxml_then = then.find('static-nat/prefix')

    def _xml_change_match_dst_addr(self, xml):
        self._rxml_match.append(
            E('destination-address',
              JXML.REPLACE,
              self.should['match_dst_addr'])
        )
        return True

    def _xml_change_match_dst_port(self, xml):
        self._rxml_match.append(
            E('destination-port', E.low(self.should['match_dst_port']))
        )
        return True

    def _xml_change_nat_addr(self, xml):
        self._rxml_then.append(E('addr-prefix', self.should['nat_addr']))
        return True

    def _xml_change_nat_port(self, xml):
        self._rxml_then.append(
            E('mapped-port', E('low', self.should['nat_port'])))
        return True

    def _xml_change_proxy_interface(self, xml):
        # this is really always going to be a 'create a new resource'. If the
        # caller is changing the 'match_dst_addr' value, then the existing
        # entry will be removed by the "hook" function.
        namevar = (self.should['proxy_interface'], self['match_dst_addr'])
        parp = NatProxyArp(self._junos, namevar)
        parp.write(touch=True)
        return True

    # -----------------------------------------------------------------------
    # Manager List, Catalog
    # -----------------------------------------------------------------------

    def _r_list(self):
        self._rlist = self.P['rules']

    def _r_catalog(self):
        get = E.security(E.nat(E.static(
            E('rule-set',
              E.name(self.P._name),
              )
        )))
        got = self.D.rpc.get_config(get)
        for rule in got.xpath('.//rule'):
            name = rule.find('name').text
            self._rcatalog[name] = {}
            self._xml_to_py(rule, self._rcatalog[name])
