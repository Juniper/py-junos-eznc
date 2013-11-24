## Device.rpc for XML API Access

The following code illustrates a basic example retrieving the inventory, and displaying the model and serial-number information.

````python
from jnpr.junos import Device

jdev = Device(user='jeremy', host='vsrx_cyan', password='jeremy1')
jdev.open()

# invoke the RPC equivalent to "show chassis hardware"

inv = jdev.rpc.get_chassis_inventory()

# use XPath expressions to extract the data from the Junos/XML response
# the :inv: variable is an lxml Element object

print "model: %s" % inv.findtext('chassis/description')
print "serial-number: %s" % inv.findtext('chassis/serial-number')

jdev.close()
````

### How to determine the RPC Command

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

### How to use the Response XML

It is very easy to determine the response of an XML API command.  On a Junos CLI you use the `| display xml` mechanism, as illustrated:
````
jeremy@jnpr-dc-fw> show chassis hardware | display xml 
<rpc-reply xmlns:junos="http://xml.juniper.net/junos/12.1X44/junos">
    <chassis-inventory xmlns="http://xml.juniper.net/junos/12.1X44/junos-chassis">
        <chassis junos:style="inventory">
            <name>Chassis</name>
            <serial-number>AD2909AA0096</serial-number>
            <description>SRX210H</description>
            <chassis-module>
                <name>Routing Engine</name>
                <version>REV 28</version>
                <part-number>750-021779</part-number>
                <serial-number>AAAH4755</serial-number>
                <description>RE-SRX210H</description>
            </chassis-module>
            <chassis-module>
                <name>FPC 0</name>
                <description>FPC</description>
                <chassis-sub-module>
                    <name>PIC 0</name>
                    <description>2x GE, 6x FE, 1x 3G</description>
                </chassis-sub-module>
            </chassis-module>
            <chassis-module>
                <name>FPC 1</name>      
                <version>REV 04</version>
                <part-number>750-023367</part-number>
                <serial-number>AAAG7981</serial-number>
                <description>FPC</description>
                <chassis-sub-module>
                    <name>PIC 0</name>
                    <description>1x T1E1 mPIM</description>
                </chassis-sub-module>
            </chassis-module>
            <chassis-module>
                <name>Power Supply 0</name>
            </chassis-module>
        </chassis>
    </chassis-inventory>
    <cli>
        <banner></banner>
    </cli>
</rpc-reply>
````

The result of the RPC command is an lxml Element, set at the first element after the `<rpc-reply>`.  In the above example, that would be `<chassis-inventory>`.  Given that, any XPath expression is relative.  So to extract the chassis serial-number, the XPath expression is simply 'chassis/serial-number'.

````python
inv = jdev.rpc.get_chassis_inventory()

print "model: %s" % inv.findtext('chassis/description')
print "serial-number: %s" % inv.findtext('chassis/serial-number')
````

Since the response variable is an LXML Element, you can use any routine available from that library.  For details, refer to the [lxml documentation](http://lxml.de/).

If XML and XPath are new to you, I would recommend the W3Schools for a quick primer.
* [XML](http://www.w3schools.com/xml)
* [XPath](http://www.w3schools.com/xpath)
