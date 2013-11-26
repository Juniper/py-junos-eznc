from . import RunstatMaker as _RSM

# internally used shortcuts

_VIEW = _RSM.View
_FIELDS = _RSM.Fields
_GET = _RSM.GetTable 
_TABLE = _RSM.Table 

RouteTable = _GET('get-route-information',
  args_key = 'destination',
  item = 'route-table/rt',
  key = 'rt-destination',
  view = _VIEW(_FIELDS()
    .str('protocol','rt-entry/protocol-name' )
    .str('via', 'rt-entry/nh/via | rt-entry/nh/nh-local-interface' )
    .end 
  )
)

RouteSummaryTable = _GET('get-route-summary-information',
  item = 'route-table',
  key = 'table-name',
  view = _VIEW(_FIELDS()
    .int('dests','destination-count')
    .int('total','total-route-count')
    .int('active','active-route-count')
    .int('holddown','holddown-route-count')
    .int('hidden','hidden-route-count')
    .table('proto', _TABLE('protocols',
        key='protocol-name',
        view=_VIEW(_FIELDS()
          .int('count','protocol-route-count')
          .int('active','active-route-count')
          .end
        )
      )
    )
    .end
  )
)

