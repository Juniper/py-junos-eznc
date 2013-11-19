from . import RunstatMaker as RSM

EthPortView = RSM.View({
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

EthPortTable = RSM.TableGetter('get-interface-information',
  args =  {'media': True, 'interface_name': '[fgx]e*' },
  item = 'physical-interface',
  view = EthPortView
)