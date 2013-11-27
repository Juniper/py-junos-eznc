from . import RunstatMaker as _RSM

# internally used shortcuts

_VIEW = _RSM.View
_FIELDS = _RSM.Fields
_GET = _RSM.GetTable 

##### -------------------------------------------------------------------------
##### illustrates the use of field groups; optimization around collecting
##### from XML child node-sets
##### -------------------------------------------------------------------------

PhyPortView = _VIEW(_FIELDS()
  .str('oper', 'oper-status')
  .str('admin','admin-status')
  .int('mtu')
  .str('link_mode','link-mode')
  .str('speed')
  .str('macaddr', 'current-physical-address')
  .end,
)

PhyPortTable = _GET('get-interface-information',
  args =  {'interface_name': '[fgx]e*' },
  args_key = 'interface_name',
  item = 'physical-interface',
  view = PhyPortView
)

### ---------------------------------------------------------------------------
### get extensive information
### ---------------------------------------------------------------------------

PhyPortStatsView = _VIEW(_FIELDS()
  .int('rx_bytes','input-bytes',  group='ts')
  .int('rx_packets', 'input-packets', group='ts')
  .int('tx_bytes','output-bytes', group='ts')
  .int('tx_packets', 'output-packets', group='ts')
  .int('rx_err_input', 'input-errors', group='in_errs')
  .int('rx_err_drops', 'input-drops', group='in_errs')
  .end,
  groups = {
    'in_errs' : 'input-error-list',
    'ts' : 'traffic-statistics'
  }
)

PhyPortStatsTable = _GET('get-interface-information',
  args =  {'extensive': True, 'interface_name': '[fgx]e*' },
  args_key = 'interface_name',
  item = 'physical-interface',
  view = PhyPortStatsView
)