from lxml import etree 
from jnpr.eznc.runstat import RunstatMaker as RSM
from jnpr.eznc.runstat.table import RunstatTable

##### =========================================================================
##### Complex demo using the Runstat classes to handle run-state/status
##### information from operational commands.  This is an experimental work
##### in progress.
##### =========================================================================

BgpTableView = RSM.View( 
  fields={
  'peers' : {
    'xpath':'bgp-peer',
    'table' : RSM.Table(
      item='bgp-peer',
      name='peer-address', 
      view = RSM.View(
        fields={
          'peer_as': {'xpath':'peer-as'},          
          'description': {'xpath': 'description' },
          'peer_state': {'xpath':'peer-state'},
          'flap_count': {'xpath':'flap-count','as_type': int },
          'ribs': {'xpath': 'bgp-rib',
            'table': RSM.Table(
              item='bgp-rib',
              view=RSM.View(
                fields={
                  'act_pf_count': {'xpath':'active-prefix-count', 'as_type': int},
                  'rx_pf_count': {'xpath':'received-prefix-count', 'as_type': int},
                  'acc_pf_count': {'xpath': 'accepted-prefix-count', 'as_type': int},
                  'sup_pf_count': {'xpath':'suppressed-prefix-count', 'as_type': int}
                })
            )}
        })
    )}
})


class BgpTable( RunstatTable ):
  GET_RPC = 'get_bgp_summary_information'
  VIEW = BgpTableView
  NAME_XPATH = None

  def get(self, **kvargs):
    # this is a hack for dev-test
    self._xml_got = etree.parse('/var/tmp/jsnap/bgp.xml').getroot()