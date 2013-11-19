from . import RunstatMaker as RSM

PhyPortView = RSM.View('PhyPortView', fields={
  'oper': { 
    'xpath': 'oper-status' },
  'admin': { 
    'xpath': 'admin-status'},
  'mtu' : {
    'xpath': 'mtu', 'as_type' : int },
  'link_mode' : { 
    'xpath': 'link-mode' },
  'speed' : { 
    'xpath': 'speed' },
  'macaddr' : {
    'xpath': 'current-physical-address' },
  'rx_bytes' : { 
    'xpath': 'ethernet-mac-statistics/input-bytes', 'as_type': int },
  'rx_packets' : {
    'xpath': 'ethernet-mac-statistics/input-packets', 'as_type': int },
  'tx_bytes' : {
    'xpath': 'ethernet-mac-statistics/output-bytes', 'as_type': int },
  'tx_packets': {
    'xpath': 'ethernet-mac-statistics/output-packets', 'as_type': int }
})

PhyPortTable = RSM.TableRpc('PhyPortTable',
  get={ 'rpc_cmd':'get_interface_information',
        'rpc_arg': {'media': True },
        'item':'physical-interface',
        'view': PhyPortView }
)