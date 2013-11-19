from lxml import etree 
from jnpr.eznc.runstat import RunstatMaker as RSM
from jnpr.eznc.runstat.table import RunstatTable

##### =========================================================================
##### Complex demo using the Runstat classes to handle run-state/status
##### information from operational commands.  This is an experimental work
##### in progress.
##### =========================================================================

BgpTableView = RSM.View({
  'peers' : {
    'table' : RSM.Table('bgp-peer', key='peer-address', 
      view = RSM.View({
        'peer_as': {'xpath':'peer-as'},          
        'description': {'xpath': 'description' },
        'peer_state': {'xpath':'peer-state'},
        'flap_count': {'xpath':'flap-count','as_type': int },
        'ribs': {
          'table': RSM.Table('bgp-rib', view=RSM.View({
            'pf_act_count': {'xpath':'active-prefix-count', 'as_type': int},
            'pf_rcv_count': {'xpath':'received-prefix-count', 'as_type': int},
            'pf_acc_count': {'xpath': 'accepted-prefix-count', 'as_type': int},
            'pf_supp_count': {'xpath':'suppressed-prefix-count', 'as_type': int}
          }))
        }
      })
    )
}})

BgpSummaryTable = RSM.GetTable('get-bgp-summary-information',
  key = None,
  view = BgpTableView
)

class TestBgpSummaryTable( BgpSummaryTable ):
  def get(self, **kvargs):
    # this is a hack for dev-test
    self._xml_got = etree.parse('/var/tmp/jsnap/bgp.xml').getroot()