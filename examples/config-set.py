import pdb
from pprint import pprint as pp 
from lxml import etree
from lxml.builder import E 

# for the example ...
from exampleutils import *
from jnpr.eznc import Netconf as Junos
from jnpr.eznc.utils import ConfigUtils

# create a junos device and open a connection

login = dict(user='jeremy', host='vsrx_cyan', password='jeremy1')
jdev = Junos(**login)
jdev.open()

jdev.ez( cu=ConfigUtils )

### someone asked how to perform configuration command using
### CLI "set" commands.  Here is a basic example. that creates
### a "raw" Junos <load-configuration> RPC.

set_commands = """
set system host-name jeremy
set system domain-name jeremy.com
"""

### This works on Junos 11.4 or later.
### I will also be adding this functionality to the "eznc"
### module, tracking github issue#13

rpc_cmd = E('load-configuration', dict(format="text", action="set"),
  E('configuration-set', set_commands )
)

rsp = jdev.rpc( rpc_cmd )

# dump the diff:
print jdev.ez.cu.diff()
# [edit system]
# -  host-name jnpr-dc-fw;
# +  host-name jeremy;
# +  domain-name jeremy.com;

print "Rolling back...."
jdev.ez.cu.rollback()


