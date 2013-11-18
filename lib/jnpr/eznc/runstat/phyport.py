from . import RunstatTable, RunstatView

__all__ = ['PhyPortTable','PhyPortView']

class PhyPortView(RunstatView):

  FIELD_XPATH = {
    'oper': 'oper-status',
    'admin' : 'admin-status',
    'mtu' : 'mtu',
    'link_mode' : 'link-mode',
    'speed' : 'speed',
    'macaddr' : 'current-physical-address',
    'rx_bytes' : 'ethernet-mac-statistics/input-bytes',
    'rx_packets' : 'ethernet-mac-statistics/input-packets',
    'tx_bytes' : 'ethernet-mac-statistics/output-bytes',
    'tx_packets' : 'ethernet-mac-statistics/output-packets'
  }

  FIELD_AS = dict(
    mtu=int, 
    rx_bytes=int, rx_packets=int,
    tx_bytes=int, tx_packets=int
  )

class PhyPortTable( RunstatTable ):
  GET_RPC = 'get_interface_information'
  GET_ARGS = dict(media=True)
  ITER_XPATH = 'physical-interface'
  VIEW = PhyPortView

### ---------------------------------------------------------------------------
### PhyPortView2 - just a sample
### ---------------------------------------------------------------------------

class PhyPortView2( PhyPortView ):
  def __init__(self,as_xml):
    PhyPortView.__init__(self,as_xml)

    with self.extend() as more:
      more.field_xpath = {
        'rx_pps' : 'traffic-statistics/input-pps',
        'tx_pps' : 'traffic-statistics/output-pps'
      }
      more.field_as = dict(rx_pps=int, tx_pps=int)
