# 3rd-party modules
from lxml.builder import E

# module packages
from jnpr.junos.cfg import Resource
from jnpr.junos import jxml as JXML


class NatSrcRule(Resource):

    """
    [edit security nat source rule-set <ruleset-name> rule <rule-name>]
    """

    PROPERTIES = [
        "match_src_addr",
        "match_dst_addr",
        "pool"
    ]

    # -----------------------------------------------------------------------
    # XML read
    # -----------------------------------------------------------------------

    def _xml_at_top(self):
        return E.security(E.nat(E.source(
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
        e = as_xml.find('src-nat-rule-match')
        to_py['match_src_addr'] = e.find('source-address').text
        to_py['match_dst_addr'] = e.find('destination-address').text
        to_py['pool'] = as_xml.find('.//pool-name').text

    # -----------------------------------------------------------------------
    # XML write
    # -----------------------------------------------------------------------

    def _xml_hook_build_change_begin(self, xml):
        """
        when doing a write, assign default values if they are not present
        """
        def _default_to(prop, value):
            if prop not in self.should:
                self.should[prop] = value

        if self.is_new:
            _default_to('match_dst_addr', '0.0.0.0/0')
            _default_to('match_src_addr', '0.0.0.0/0')

    def _xml_change_match_src_addr(self, xml):
        xml.append(E('src-nat-rule-match',
                     E('source-address',
                       JXML.REPLACE,
                       self.should['match_src_addr'])
                     ))
        return True

    def _xml_change_match_dst_addr(self, xml):
        xml.append(E('src-nat-rule-match',
                     E('destination-address',
                       JXML.REPLACE,
                       self.should['match_dst_addr'])
                     ))
        return True

    def _xml_change_pool(self, xml):
        xml.append(E.then(
            E('source-nat', E.pool(E('pool-name', self.should['pool'])))
        ))
        return True

    # -----------------------------------------------------------------------
    # Manager List, Catalog
    # -----------------------------------------------------------------------

    def _r_list(self):
        self._rlist = self.P['$rules']

    def _r_catalog(self):
        get = E.security(E.nat(E.source(
            E('rule-set',
              E.name(self.P._name),
              )
        )))
        got = self.D.rpc.get_config(get)
        for rule in got.xpath('.//rule'):
            name = rule.find('name').text
            self._rcatalog[name] = {}
            self._xml_to_py(rule, self._rcatalog[name])
