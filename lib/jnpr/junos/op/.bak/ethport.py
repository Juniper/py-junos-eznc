from . import RunstatMaker as _RSM

# internally used shortcuts

_VIEW = _RSM.View
_FIELDS = _RSM.Fields
_GET = _RSM.GetTable 
_TABLE = _RSM.Table 

##### -------------------------------------------------------------------------
##### illustrates the use of field groups; optimization around collecting
##### from XML child node-sets
##### -------------------------------------------------------------------------

EthPortView = _VIEW(_FIELDS()
  .str('oper', 'oper-status')
  .str('admin','admin-status')
  .int('mtu')
  .str('link_mode','link-mode')
  .str('speed')
  .str('macaddr','current-physical-address')
  .int('rx_bytes', 'input-bytes', group='mac_stats')
  .int('rx_packets', 'input-packets', group='mac_stats')
  .int('tx_bytes', 'output-bytes', group='mac_stats')
  .int('tx_packets', 'output-packets', group='mac_stats')
  .end,
  groups = {
    'mac_stats':'ethernet-mac-statistics'
  }
)

EthPortTable = _GET('get-interface-information',
  args =  {'media': True, 'interface_name': '[fgx]e*' },
  args_key = 'interface_name',
  item = 'physical-interface',
  view = EthPortView
)

##### The following shows how to declare a new View class that
##### extends from another.

EthPortView2 = _VIEW( extends=EthPortView, 
  fields = _FIELDS()
    .flag('present', 'ifdf-present', group='flags')
    .flag('running', 'ifdf-running', group='flags')
    .astype('loopback', astype=lambda x: bool(x == 'enabled'))
    .end,
  groups = {'flags':'if-device-flags'}
)
