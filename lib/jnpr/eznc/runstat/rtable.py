from . import RunstatMaker as RSM

RouteView= RSM.View(
  fields={
    'protocol' : {'xpath': 'rt-entry/protocol-name'},
    'via' : {'xpath':'rt-entry/nh/via | rt-entry/nh/nh-local-interface' }
  })

RouteTable = RSM.TableRpc('RouteTable',
  get={ 'rpc_cmd':'get_route_information',
        'item':'route-table/rt',
        'name':'rt-destination',
        'view': RouteView }
  )

