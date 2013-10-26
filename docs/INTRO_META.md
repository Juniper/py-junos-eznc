# RPC Metaprogramming

The following code illustrates a basic example of opening a NETCONF connection to a device, retrieving the inventory, and displaying the model and serial-number information.

````python
from jnpr.eznc import Netconf

jdev = Netconf(user='jeremy', host='vsrx_cyan', password='jeremy1')
jdev.open()

# invoke the RPC equivalent to "show chassis hardware"

inv = jdev.rpc.get_chassis_inventory()

# use XPath expressions to extract the data from the Junos/XML response
# the :inv: variable is an lxml Element object

print "model: %s" % inv.find('chassis/description').text
print "serial-number: %s" % inv.find('chassis/serial-number').text

# model: JUNOSV-FIREFLY
# serial-number: cf2eaceba2b7

jdev.close()

````

It is very easy to determine an XML API command.  On a Junos CLI you use the `| display xml rpc` mechanism, as illustrated:
````
jeremy@jnpr-dc-fw> show chassis hardware | display xml rpc 
<rpc-reply xmlns:junos="http://xml.juniper.net/junos/12.1X44/junos">
    <rpc>
        <get-chassis-inventory>
        </get-chassis-inventory>
    </rpc>
    <cli>
        <banner></banner>
    </cli>
</rpc-reply>
````

The contents between the `rpc` elements is the XML RPC command, in this case `get-chassis-inventory`.  As you can see from the above code example, to invoke this API, use the Netconf object `rpc` attribute and invoke a method name corresponding to the XML RPC command.  If the command has dashes ('-') then swap to underbars ('_').  
````python
inv = jdev.rpc.get_chassis_inventory()
````

If the command has parameters, you do the same.  Here is an example retrieving the status of a given interface:
````
jeremy@jnpr-dc-fw> show interfaces ge-0/0/0 media | display xml rpc 
<rpc-reply xmlns:junos="http://xml.juniper.net/junos/12.1X44/junos">
    <rpc>
        <get-interface-information>
                <media/>
                <interface-name>ge-0/0/0</interface-name>
        </get-interface-information>
    </rpc>
    <cli>
        <banner></banner>
    </cli>
</rpc-reply>
````
The equivalent python would look like this:
````python
rsp = jdev.rpc.get_interface_information( media=True, interface_name='ge-0/0/0' )
````
Here the `media` parameter does not take a value, so you simple assign it to `True`.  Again, for parameter names that contain dashesh, you swap them for underbars; `interface-name` becomes `interface_name`.
