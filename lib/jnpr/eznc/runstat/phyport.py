from . import RunstatTable, RunstatView

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

