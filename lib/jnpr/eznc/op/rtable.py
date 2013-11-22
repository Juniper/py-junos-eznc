from . import RunstatMaker as RSM

RouteTable = RSM.GetTable('get-route-information',
  args_key = 'destination',
  item = 'route-table/rt',
  key = 'rt-destination',
  view = RSM.View(RSM.Fields()
    .str('protocol','rt-entry/protocol-name' )
    .str('via', 'rt-entry/nh/via | rt-entry/nh/nh-local-interface' )
    .end 
  )
)

RouteSummaryTable = RSM.GetTable('get-route-summary-information',
  item = 'route-table',
  key = 'table-name',
  view = RSM.View(RSM.Fields()
    .int('dests','destination-count')
    .int('total','total-route-count')
    .int('active','active-route-count')
    .int('holddown','holddown-route-count')
    .int('hidden','hidden-route-count')
    .table('proto', RSM.Table('protocols',
        key='protocol-name',
        view=RSM.View(RSM.Fields()
          .int('count','protocol-route-count')
          .int('active','active-route-count')
          .end
        )
      )
    )
    .end
  )
)

