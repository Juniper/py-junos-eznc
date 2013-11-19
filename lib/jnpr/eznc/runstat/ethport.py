from . import RunstatMaker as RSM

##### -------------------------------------------------------------------------
##### illustrates the use of field groups; optimization around collecting
##### from XML child node-sets
##### -------------------------------------------------------------------------

EthPortView = RSM.View(RSM.Fields()
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

EthPortTable = RSM.TableGetter('get-interface-information',
  args =  {'media': True, 'interface_name': '[fgx]e*' },
  item = 'physical-interface',
  view = EthPortView
)