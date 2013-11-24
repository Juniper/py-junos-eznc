## Operation Table Views

A Table _View_ defines the mapping between the Junos/XML and the field names by which you want to retrieve the data.

````python
>>> from jnpr.junos.op.ethport import *
>>> eths = EthPortTable(dev).get()
>>> e1 = eths[1]
>>> e1
RunstatView:ge-0/0/1
````

If we want to get a list of the know View keys, we can:
````python
>>> pprint( e1.keys() )
['oper',
 'tx_bytes',
 'rx_packets',
 'macaddr',
 'rx_bytes',
 'link_mode',
 'admin',
 'tx_packets',
 'speed',
 'mtu']
````

If we want to obtain a tuple list of the key/value items:
````python
>>> pprint( e1.items() )
[('oper', 'up'),
 ('tx_bytes', 0),
 ('rx_packets', 20759),
 ('macaddr', '00:0c:29:eb:a2:c1'),
 ('rx_bytes', 2415792),
 ('link_mode', 'Full-duplex'),
 ('admin', 'up'),
 ('tx_packets', 0),
 ('speed', '1000mbps'),
 ('mtu', 1518)]
````

But generally speaking, we will just access the items that we want as if they were a variable property:
````python
>>> e1.mtu
1518
>>> e1.oper
'up'
````

### Changing a View

There are two ways to change a view: (1) by changing the _Table.view_ and access a new view, or (2) by using the _View.asview()_ routine.

Using the _Table.view_ property.  Here we are chaging the Table view to `EthPortView2`.  This view contain additional fields like "loopback" and "running".

````python
>>> eths.view = EthPortView2
>>> e1 = eths[1]
>>> pprint( e1.items() )
[('oper', 'up'),
 ('rx_packets', 20759),
 ('macaddr', '00:0c:29:eb:a2:c1'),
 ('rx_bytes', 2415792),
 ('loopback', False),
 ('admin', 'up'),
 ('speed', '1000mbps'),
 ('mtu', 1518),
 ('running', True),
 ('link_mode', 'Full-duplex'),
 ('tx_bytes', 0),
 ('tx_packets', 0),
 ('present', True)]

````

And by using the _View.asview()_ routine:
````python
>>> v2 = e1.asview(EthPortView2)
>>> pprint( v2.items() )
[('oper', 'up'),
 ('rx_packets', 20759),
 ('macaddr', '00:0c:29:eb:a2:c1'),
 ('rx_bytes', 2415792),
 ('loopback', False),
 ('admin', 'up'),
 ('speed', '1000mbps'),
 ('mtu', 1518),
 ('running', True),
 ('link_mode', 'Full-duplex'),
 ('tx_bytes', 0),
 ('tx_packets', 0),
 ('present', True)]
````

### Creating Your Own Views

It is very easy to create your own Views.  Take a look at the existing code in the [_ops directory](../../ops).  Additional documentation will be written on this topic in the near future.  The _Junos EZ_ library was written so that it would take you less than 10 minutes to write your own Views.
