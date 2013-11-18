from . import RunstatTable, RunstatView

__all__ = ['PhyPortTable','PhyPortView','PhyPortView2']

class PhyPortTable( RunstatTable ):
  GET_RPC = 'get_interface_information'
  GET_ARGS = dict(media=True)
  ITER_XPATH = 'physical-interface'

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

  FIELD_AS_INT = [
    'mtu','rx_bytes','rx_packets',
    'tx_bytes','tx_packets'
  ]

class PhyPortView2( PhyPortView ):
  def __init__(self,as_xml):
    PhyPortView.__init__(self,as_xml)

    new_fields = {
      'rx_pps' : 'traffic-statistics/input-pps',
      'tx_pps' : 'traffic-statistics/output-pps'
    }

    with self.extend() as more:
      more.field_xpath = dict(new_fields)
      more.field_as_int = new_fields.keys()
