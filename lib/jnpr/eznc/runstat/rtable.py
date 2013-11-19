from . import RunstatMaker as RSM

RouteTable = RSM.TableGetter('get-route-information',
  item = 'route-table/rt',
  key = 'rt-destination',
  view = RSM.View(RSM.Fields()
    .str('protocol','rt-entry/protocol-name' )
    .str('via', 'rt-entry/nh/via | rt-entry/nh/nh-local-interface' )
    .end 
  )
)

