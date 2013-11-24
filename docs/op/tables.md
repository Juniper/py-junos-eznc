## Operational Tables

You can associate a _Table_ with a _Device_ using the same methods described [here](../device.md).  So the following are equivalent.

As a standalone variable:
````python
>>> from jnpr.junos.op.ethport import *
>>> eths = EthPortTable(dev)
>>> eths.get()
RunstatGetTable.get-interface-information:jnpr-dc-fw: 3 items
>>> eths.keys()
['ge-0/0/0', 'ge-0/0/1', 'ge-0/0/2']
````
and as a bound property:
````python
>>> from jnpr.junos.op.ethport import *
>>> eths = EthPortTable(dev)
>>> eths.get()
RunstatGetTable.get-interface-information:jnpr-dc-fw: 3 items
>>> eths.keys()
['ge-0/0/0', 'ge-0/0/1', 'ge-0/0/2']
>>> dev.bind(eths=EthPortTable)
>>> dev.eths.get()
RunstatGetTable.get-interface-information:jnpr-dc-fw: 3 items
>>> dev.eths.keys()
['ge-0/0/0', 'ge-0/0/1', 'ge-0/0/2']
````

### Retrieving Table Data

You use the _Table.get()_ routine to load the table data from the Junos device.  The Table is defined to perform the necessary Junos XML API call as pass any default parameters that are necessary, so you don't need to know them.

There are cases, however, that knowing a little bit more comes in handy.  You **can** pass any valid Junos command argument to the _Table.get()_ routine.  For example, the _RouteTable_ will load all of the routes, equivalent to the command "show routes":

````python
>>> from jnpr.junos.op.rtable import RouteTable
>>> routes = RouteTable(dev).get()
>>> routes
RunstatGetTable.get-route-information:jnpr-dc-fw: 147 items
````
There are 147 routes on this device.  

But let's say all we wanted were those that matched against the destination "192.168.56.0/24".   From the Junos CLI, we would do:

````
jeremy@jnpr-dc-fw> show route 192.168.56.0/24 

inet.0: 147 destinations, 147 routes (147 active, 0 holddown, 0 hidden)
+ = Active Route, - = Last Active, * = Both

192.168.56.0/24    *[Direct/0] 4d 09:05:40
                    > via ge-0/0/0.0
192.168.56.10/32   *[Local/0] 4d 09:05:45
                      Local via ge-0/0/0.0

jeremy@jnpr-dc-fw>
````

We can get the actual Junos XML RPC command using the `|display xml rpc` filter, like so:
````
jeremy@jnpr-dc-fw> show route 192.168.56.0/24 | display xml rpc 
<rpc-reply xmlns:junos="http://xml.juniper.net/junos/12.1I0/junos">
    <rpc>
        <get-route-information>
                <destination>192.168.56.0/24</destination>
        </get-route-information>
    </rpc>
    <cli>
        <banner></banner>
    </cli>
</rpc-reply>
````
So we can see that this command takes an argument `<destination>`.  Since the _RouteTable_ invokes `<get-route-information>`, we can pass the same argument to get the same results:

````python
>>> routes.get(destination="192.168.56.0/24")
RunstatGetTable.get-route-information:jnpr-dc-fw: 2 items
````

### Access Table Items

You can treat a _Table_ like a Python dictonary, so you have the following routines:

* keys() - get a list of table item names
* values() - get a list of tuples(name/value) for each field in each record
* items() - a tuple composite of keys() and values()

````python
>>> routes.keys()
['192.168.56.0/24', '192.168.56.10/32']
>>> 
>>> pprint( routes.values() )
[[('via', 'ge-0/0/0.0'), ('protocol', 'Direct')],
 [('via', 'ge-0/0/0.0'), ('protocol', 'Local')]]
>>> 
>>> pprint( routes.items() )
[('192.168.56.0/24', [('via', 'ge-0/0/0.0'), ('protocol', 'Direct')]),
 ('192.168.56.10/32', [('via', 'ge-0/0/0.0'), ('protocol', 'Local')])]
>>> 
````

You can get a _View_ of a table item by making a selection either by name (key) or index.  

````python
# get the first route in the table:
>>> first = routes[0]
>>> first
RunstatView:192.168.56.0/24

# get a named route from the table:
>>> this = routes['192.168.56.10/32']
>>> this
RunstatView:192.168.56.10/32
````
