# ABOUT

STATUS: ___WORK IN PROGRESS - UNDER ACTIVE DEVELOPMENT___

A Python module that makes automating Junos devices over the NETCONF API "easy".  The goal of this "microframework" is to enable Netops/engineers the ability to create Python scripts without requiring "hardcore" programming knownledge.  This module is not specifically tied to any version of Junos or any Junos product family. This goal of this module is to provide a general purpose set of utilities and resources.  The module has been designed so that future contributors can easily "plug-in" thier extensions.  This module should work with __ALL__ Junos based products.  

There are three basic "layers" to this module: Resources, Utilities, and RPC Metaprogramming

#### Managing Resources as Abstractions

Resources are defined as elements of the Junos configuration that you want to manage as discrete items.  For example, a SRX security zone has an address-book, that it turn contains a list of address items and a list of address-sets.  The purpose of the resource abstraction is to enable the programmer to manage these items as simple Python objects, and not requiring kownledge of the underlying Junos/XML. 

Resources can be Junos product family specifc.  Security Zones, for example, would be found only on SRX products.

For the catalog of Resources provided by this module, see [here](docs/RESOURCE_CATALOG.md).

For a quick intro on using Resources, see [here](docs/INTRO_RESOURCES.md).


#### Utility Libraries

An application will often want to perform common fucntions, and again wihtout requiring knowledge of the underlying Junos/XML.  Examples of these libraries include: filesystem, routing-engine, and config.  The config library, for example, allows you to do things like "rolllback", "commit check" and "show | compare" to get a diff-patch output of candidate changes.

For the catalog of Utility libraries provided by this module, see [here](docs/UTILS_CATALOG.md).

For a quick intro on using utility libraries, see [here](docs/INTRO_UTILS.md).

#### RPC Metaprogramming 

You should always have the ability to "do anything" that the Junos/XML API provides.  This module attempts to make accessing Junos at this low-level "easy".  The term "metaprogramming" basically means that this module will dynamically create Junos XML Remote Procdure Calls (RPCs) as you invoke them from your program, rather that pre-coding them as part of the module distribution.  Said another way, if Junos provides thousands of RPCs, this module does *not* contain thousands of RPC functions.  It metaprogramms only the RPCs that you use, keeping the size of this module small, and the portability flexible.

For a quick intro on using RPC metaprogramming, see [here](docs/INTRO_META.md).

# INSTALLATION

See [here](INSTALL.md) for installation instructions.

## QUICK EXAMPLES

### Resource Abstrations

The following code example illustrates how to use the SRX "ZoneAddrBook" resource to add a new address item to a zone's address book.

````python
from pprint import pprint

from jnpr.eznc import Netconf
from jnpr.eznc.resources.srx import ZoneAddrBook

jdev = Netconf(user='jeremy', host='vsrx_cyan', password='jeremy1')
jdev.open()

# bind an AddrBook class to this Netconf instance.  this
# will create an instance of the AddrBook automatically
# and create an attribute called 'ab' on the Netconf instance

jdev.bind( ab=ZoneAddrBook )

# now select the address book for a specific security zone
# this will load the contents of the address book from the
# Junos SRX device

this_ab = jdev.ab["TRUST"]

# an address book manages two resources, the list of address 
# items, and the list of address-sets.  You can see what 
# a specific resource manages by looking at the :manages:
# property

pprint( this_ab.manages )
#>>> ['addr', 'set']

# lets add a new address item called 'JEREMY-HOST' with
# and IP address of '192.168.1.1'

jeremy = this_ab.addr['JEREMY-HOST']

# does this address item already exist?  all resources
# have a property called :exists: that returns True or False
# indicating whether or not the resource exists in the 
# Junos configuration

pprint( jeremy.exists )
#>>> False

# each resource has a list of properties that you can
# read/write.  You can see this list by examining the
# :properties: attribute

pprint( jeremy.properties )
#>>> ['_exists', '_active', 'description', 'ip_prefix']

# the :_exists: and :_active: items are 'meta-properties'
# controlled by the resource framework; so don't touch 
# these.  The other properties :description: and
# :ip_prefix: are for you to control.  So let's set
# these for our new address

jeremy['description'] = "Jeremy's laptop computer"
jeremy['ip_prefix'] = '192.168.1.1'

# now store these values to the Junos devices.  this 
# action does *NOT* commit the configuration, only
# sets the values, much like doing the "set" commands
# at the Junos CLI

jeremy.write()

# if we were to examine the Junos CLI configuration
# we can see that the change has been loaded into 
# the candidate configuration
# [edit]
# jeremy@jnpr-dc-fw# show | compare 
# [edit security zones security-zone TRUST address-book]
#        address BOB-HOST { ... }
# +      address JEREMY-HOST {
# +          description "Jeremy's laptop computer";
# +          192.168.1.1/32;
# +      }
````

For more details on the Resource framework, see [here](docs/INTRO_RESOURCES.md).

### Utility Libraries

Utility libraries are collections of functions.  The following illustrates the ConfigUtils library on checking configuration changes and displaying the diff.  This example is a continuation of the prior section.
````python
from jnpr.eznc.utils import ConfigUtils

# now bind the ConfigUtils to this Netconf instance, creating an attribute
# called :cu:

jdev.bind(cu=ConfigUtils)

# now use the ConfigUtils to do a "commit check".  If the candidate configuration is
# OK, then this will return :True: and if not will return a dictionary of error information

jdev.cu.commit_check()
#>>> True

# we can obtain a copy of the "diff" string, which is the equivalent of the Junos CLI
# command "show | compare"

print jdev.cu.diff()
#>>> [edit security zones security-zone TRUST address-book]
#>>>        address BOB-HOST { ... }
#>>> +      address JEREMY-HOST {
#>>> +          description "Jeremy's laptop computer";
#>>> +          192.168.1.1/32;
#>>> +      }

# now we can either commit these changes or discard them.  showing how to
# discard them using the rollback function.

jdev.cu.rollback()
````
### RPC Metaprogramming

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
For more information on RPC metaprogramming, see [here](docs/INTRO_META.md).

# DEPENDENCIES

  * [Python 2.7](http://www.python.org/) - could work with others, but I haven't tested it
  * [ncclient](https://github.com/juniper/ncclient) (_Juniper edition_) - NETCONF base library
  * [lxml](http://lxml.de/index.html) - XML programming library
  * [jinja2](http://jinja.pocoo.org/docs) - templating library

# LICENSE

  BSD-2
  
# CONTRIBUTORS

  - Jeremy Schulman, @nwkautomaniac
