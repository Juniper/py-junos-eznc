from lxml import etree 
from jnpr.eznc.runstat import *

# -----------------------------------------------------------------------------
# toplevel bgp-peer table
# -----------------------------------------------------------------------------

class BgpPeerTableViewRibTableView( RunstatView ):
  FIELD_XPATH = dict(
    act_pf_count = 'active-prefix-count',
    rx_pf_count = 'received-prefix-count',
    acc_pf_count = 'accepted-prefix-count',
    sup_pf_count = 'suppressed-prefix-count'
  )
  FIELD_AS = dict(
    act_pf_count = int,
    rx_pf_count = int,
    acc_pf_count = int,
    sup_pf_count = int
  )

class BgpPeerTableViewRibTable( RunstatTable ):
  ITER_XPATH = 'bgp-rib'
  VIEW = BgpPeerTableViewRibTableView

class BgpPeerTableView( RunstatView ):
  FIELD_XPATH = dict(
    peer_as='peer-as',
    description='description',
    peer_state='peer-state',
    flap_count='flap-count',
    ribs='bgp-rib'
  )
  FIELD_AS = dict(
    flap_count=int,
    ribs=BgpPeerTableViewRibTable
  )

class BgpPeerTable( RunstatTable ):
  ITER_XPATH = 'bgp-peer'    
  NAME_XPATH = 'peer-address'
  VIEW = BgpPeerTableView

# -----------------------------------------------------------------------------
# toplevel bgp-rib table
# -----------------------------------------------------------------------------

class BgpRibTable( RunstatTable ):
  ITER_XPATH = 'bgp-rib'    

# -----------------------------------------------------------------------------
# toplevel bgp table
# -----------------------------------------------------------------------------

class BgpTableView(RunstatView):
  FIELD_XPATH = dict(
    peers = 'bgp-peer',
    ribs = 'bgp-rib'
  )
  FIELD_AS = dict(
    peers = BgpPeerTable,
    ribs = BgpRibTable
  )

class BgpTable( RunstatTable ):
  GET_RPC = 'get_bgp_summary_information'
  VIEW = BgpTableView

  def get(self, **kvargs):
    # this is a hack for dev-test
    self._xml_got = etree.parse('/var/tmp/jsnap/bgp.xml').getroot()
