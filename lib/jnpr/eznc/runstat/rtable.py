from . import RunstatMaker as RSM

RouteView = RSM.View({
  'protocol' : {'xpath': 'rt-entry/protocol-name'},
  'via' : {'xpath':'rt-entry/nh/via | rt-entry/nh/nh-local-interface' }
})

RouteTable = RSM.TableGetter('get-route-information',
  item = 'route-table/rt',
  key = 'rt-destination',
  view = RouteView 
)

