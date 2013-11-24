## Getting Operational / Run-State Data

Operational, or "run-state", data refers not to the configuration of the device, but rather the status of information.  From the Junos CLI, this information is obtained using "show" commands, like "show interfaces".  Gathering operaitonal information is a critical function of automating network infrastrcutre.  The _Junos EZ_ library provides two abstractions to facilitate getting this data: _Tables_ and _Views_.

### Overivew

#### Tables

The concept of a table is nothing new, taking it from the world of databases.  So if you think of the Junos OS having a "Operational Database", then that database contains a collection of tables.  For example the "show route" command could provide the route _table_ and "show interfaces media [fgx]e*" could provide the Ethernet port _table_.

Each table has a collection of items (database 'records').  Each item has a unique key (name).  The item data can be examined as a _View_.

#### Views

Think of a view the same way you would think of the Junos CLI options "brief","terse","detail","extensive".  The underlying data (table record) that Junos provides is the same.  The Junos CLI simply applies a different "view" to that data and renders the data in human readable form (aka. "CLI output").

The purpose of a _View_ in the _Junos EZ_ library is to present the table item feilds in a native Python syntax.  By doing this, the user does not need to know anything specific about Junos or the underlying Junos XML API.

### Example

The following is an example of the examinging the "Ethernet Port Table".
````python
>>> from jnpr.junos.op.ethport import EthPortTable
>>> eths = EthPortTable(dev)
>>> eths.get()
RunstatGetTable.get-interface-information:vsrx_cyan: 3 items
>>> 
>>> eths.keys()
['ge-0/0/0', 'ge-0/0/1', 'ge-0/0/2']
>>> 
>>> e1 = eths['ge-0/0/1']
>>> 
>>> pprint( e1.items() )
[('oper', 'up'),
 ('tx_bytes', 0),
 ('rx_packets', 20381),
 ('macaddr', '00:0c:29:eb:a2:c1'),
 ('rx_bytes', 2368928),
 ('link_mode', 'Full-duplex'),
 ('admin', 'up'),
 ('tx_packets', 0),
 ('speed', '1000mbps'),
 ('mtu', 1518)]
>>> 
>>> e1.admin
'up'
>>> e1.oper
'up'
>>> e1.rx_bytes
2368928

````
