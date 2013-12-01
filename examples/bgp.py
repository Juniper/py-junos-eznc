from lxml import etree 
from jnpr.junos.runstat import RunstatMaker as RSM

##### =========================================================================
##### Complex demo using the Runstat classes to handle run-state/status
##### information from operational commands.  This is an experimental work
##### in progress.
##### =========================================================================

BgpTableView = RSM.View(RSM.Fields()
  .table('peers', RSM.Table('bgp-peer', 
    key='peer-address', 
    view = RSM.View(RSM.Fields()
      .str('peer_as','peer-as')
      .str('description')
      .str('peer_state','peer-state')
      .int('flap_count', 'flap-count')
      .table('ribs',RSM.Table('bgp-rib', 
        view=RSM.View(RSM.Fields()
          .int('pf_act_count','active-prefix-count')
          .int('pf_rcv_count','received-prefix-count')
          .int('pf_acc_count','accepted-prefix-count')
          .int('pf_supp_count','suppressed-prefix-count')
          .end )
      ))
      .end )
  ))
  .end )

BgpSummaryTable = RSM.GetTable('get-bgp-summary-information',
  key = None,
  view = BgpTableView
)

class TestBgpSummaryTable( BgpSummaryTable ):
  def get(self, **kvargs):
    # this is a hack for dev-test
    self._xml_got = etree.parse('/var/tmp/jsnap/bgp.xml').getroot()
