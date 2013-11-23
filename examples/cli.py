
from pprint import pprint as pp 
from lxml import etree

# for the example ...
from exampleutils import *
from jnpr.junos import Device as Junos

login = dict(user='jeremy', host='vsrx_cyan', password='jeremy1')
jdev = Junos(**login)
jdev.open()

# you can run any cli command using the :cli: method, for example
print "showing command: 'show version'"
print jdev.cli("show version")

# showing command: 'show version'

# Hostname: jnpr-dc-fw
# Model: junosv-firefly
# JUNOS Software Release [12.1X44-D10.4]


# you can also obtain the XML RPC for the associated command by 
# doing this:

print "showing as XML RPC command:"
xml_cmd = jdev.cli("show version | display xml rpc")

# this is an actual XML element, so we can dump it for debug:
etree.dump(xml_cmd)

# showing as XML RPC command:
# <get-software-information>
# </get-software-information>

# you can then take that output then feed it back into the :rpc: metaexec

cmd_rsp = jdev.rpc( xml_cmd )

# now dump the XML response output;

print "showing as XML RPC response:"
etree.dump( cmd_rsp )

# showing as XML RPC response:
# <software-information>
# <host-name>jnpr-dc-fw</host-name>
# <product-model>junosv-firefly</product-model>
# <product-name>junosv-firefly</product-name>
# <package-information>
# <name>junos</name>
# <comment>JUNOS Software Release [12.1X44-D10.4]</comment>
# </package-information>
# </software-information>

# of course, you could have gotten the exact same thing:
print "And again another way ..."

xml_rsp = jdev.cli( "show version", format='xml' )
etree.dump(xml_rsp)

# but the 'rigth' way to invoke XML commands is to use
# the :rpc: as the metaexec as intented, such as:

xml_rsp = jdev.rpc.get_software_information();
print "And again using meta rpc"
etree.dump(xml_rsp)

jdev.close()
