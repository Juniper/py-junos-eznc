# 3rd-party modules
from lxml.builder import E

# module packages
from jnpr.junos.cfg import Resource
from jnpr.junos import jxml as JXML
from jnpr.junos.cfg.srx.nat.nat_st_rule import NatStaticRule


class NatStaticRuleSet(Resource):

    """
    [edit security nat static rule-set <name>]
    """

    PROPERTIES = [
        "description",
        "zone_from",
        "$rules",
        "$rules_count"
    ]

    def __init__(self, junos, name=None, **kvargs):
        if name is None:
            # resource-manager
            Resource.__init__(self, junos, name, **kvargs)
            return

        self.rule = NatStaticRule(junos, M=self, parent=self)
        self._manages = ['rule']
        Resource.__init__(self, junos, name, **kvargs)

    # -----------------------------------------------------------------------
    # XML read
    # -----------------------------------------------------------------------

    def _xml_at_top(self):
        return E.security(E.nat(E.static(
            E('rule-set', E.name(self._name))
        )))

    def _xml_hook_read_begin(self, xml):
        """
        need to add the <from>,<to> elements to pick up the zone context
        need to add the rules, names-only
        """
        rs = xml.find('.//rule-set')
        rs.append(E('from'))
        rs.append(E.rule(JXML.NAMES_ONLY))
        return True

    def _xml_at_res(self, xml):
        return xml.find('.//rule-set')

    def _xml_to_py(self, as_xml, to_py):
        Resource._r_has_xml_status(as_xml, to_py)
        Resource.copyifexists(as_xml, 'description', to_py)
        to_py['zone_from'] = as_xml.find('from/zone').text
        to_py['$rules'] = [rule.text for rule in as_xml.xpath('.//rule/name')]
        to_py['$rules_count'] = len(to_py['$rules'])

    # -----------------------------------------------------------------------
    # XML write
    # -----------------------------------------------------------------------

    def _xml_change_zone_from(self, xml):
        xml.append(E('from', JXML.REPLACE, E.zone(self.should['zone_from'])))
        return True

    # -----------------------------------------------------------------------
    # Resource List, Catalog
    # -- only executed by 'manager' resources
    # -----------------------------------------------------------------------

    def _r_list(self):
        get = E.security(E.nat(E.static(
            E('rule-set', JXML.NAMES_ONLY)
        )))
        got = self.D.rpc.get_config(get)
        self._rlist = [name.text for name in got.xpath('.//name')]

    def _r_catalog(self):
        get = E.security(E.nat(E.static(
            E('rule-set')
        )))
        got = self.D.rpc.get_config(get)
        for ruleset in got.xpath('.//rule-set'):
            name = ruleset.find("name").text
            self._rcatalog[name] = {}
            self._xml_to_py(ruleset, self._rcatalog[name])
