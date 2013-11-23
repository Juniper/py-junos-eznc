# STATUS

[![Build Status](https://travis-ci.org/jeremyschulman/py-junos-eznc.png?branch=master)](https://travis-ci.org/jeremyschulman/py-junos-eznc)

The repo is under active development on release 0.0.2.  If you take a clone, you are getting the latest, and perhaps not entirely stable code.  For tagged releases, please see [here](https://github.com/jeremyschulman/py-junos-eznc/tags).
# ABOUT

A Python module that makes automating Junos devices over the NETCONF API "easy".  The goal of this "microframework" is to enable Netops/engineers the ability to create Python scripts without requiring "hardcore" programming knownledge.  

This module is not specifically tied to any version of Junos or any Junos product family. It provides a general purpose set of utilities and resources abstrations.  It has been designed so that future contributors can easily "plug-in" thier extensions. 

There are three basic "layers" to this module: Resources, Utilities, and RPC Metaprogramming

#### Managing Resources Abstractions

Resources are defined as elements of the Junos configuration that you want to manage as discrete items.  For example, a SRX security zone has an address-book, that it turn contains a list of address items and a list of address-sets.  The purpose of the resource abstraction is to enable the programmer to manage these items as simple Python objects, and not requiring kownledge of the underlying Junos/XML.  Resources can be Junos product family specifc.  Security Zones, for example, would be found only on SRX products.

For a quick intro on using Resources, see [here](docs/INTRO_RESOURCES.md).

For the catalog of Resources provided by this module, see [here](docs/RESOURCE_CATALOG.md).

#### Utility Libraries

An application will often want to perform common fucntions, and again wihtout requiring knowledge of the underlying Junos/XML.  The ConfigUtils library, for example, allows you to do things like "rolllback", "commit check" and "show | compare" to get a diff-patch output of candidate changes.

For a quick intro on using utility libraries, see [here](docs/INTRO_UTILS.md).

For the catalog of Utility libraries provided by this module, see [here](docs/UTILS_CATALOG.md).

#### RPC Metaprogramming 

You should always have the ability to "do anything" that the Junos/XML API provides.  This module attempts to make accessing Junos at this low-level "easy".  The term "metaprogramming" basically means that this module will dynamically create Junos XML Remote Procdure Calls (RPCs) as you invoke them from your program, rather that pre-coding them as part of the module distribution.  Said another way, if Junos provides thousands of RPCs, this module does *not* contain thousands of RPC functions.  It metaprogramms only the RPCs that you use, keeping the size of this module small, and the portability flexible.

For a quick intro on using RPC metaprogramming, see [here](docs/INTRO_META.md).

# INSTALLATION

I am currently in the process of building a "proper" setup.py file.  In the meantime, please bear with me.

To install this module, you will first need to download and install the [ncclient](https://github.com/juniper/ncclient) module from the Juniper github repo directly.  Follow the instructions there for details.

Once you've done that, you can then install this module using:

````shell
[py-junos-eznc] python setup.py install
````

Once you've done that you should be able to verify the installation via the python shell:

````python
import jnpr.eznc

print jnpr.eznc.VERSION
````

## QUICK EXAMPLES

### FACTS

Each managed Junos/NETCONF instance maintains a dictionary of "facts".  These facts are loaded when your program opens a connetion to the device.  Facts are generally static pieces of information, such as the software version or serial-number.  

The following example simply dumps the facts to the screen:

````python
from pprint import pprint
from jnpr.eznc import Netconf

jdev = Netconf(user='jeremy', host='vsrx_cyan', password='jeremy1')
jdev.open()

pprint(jdev.facts)
#>>> {'RE0': {'last_reboot_reason': 'Router rebooted after a normal shutdown.',
#>>>          'model': 'JUNOSV-FIREFLY RE',
#>>>          'status': 'Testing',
#>>>          'up_time': '2 days, 3 hours, 33 minutes, 50 seconds'},
#>>>  'domain': 'wfs.com',
#>>>  'fqdn': 'jnpr-dc-fw.wfs.com',
#>>>  'model': 'FIREFLY-PERIMETER',
#>>>  'hostname': 'jnpr-dc-fw',
#>>>  'ifd_style': 'CLASSIC',
#>>>  'personality': 'SRX_BRANCH',
#>>>  'serialnumber': 'cf2eaceba2b7',
#>>>  'switch_style': 'NONE',
#>>>  'version': '12.1X44-D10.4',
#>>>  'version_info': junos.versino_info(major=(12, 1), type=X, minor=44-D10, build=4),
#>>>  'virtual': True}

jdev.close()
````

The 'version_info' can be used for version comparions.  For example:
````python

# Is this version earlier than "11.4"?

jdev.facts['version_info'] < (11,4)
#>>> False

# Is this version later that "12.0"?

jdev.facts['version_info'] > (12,0)
#>>> True
````

If you need to refresh the facts for any reason, you can invoke the `facts_refresh()` method on the Netconf instance, as illustrated:

````python
jdev.facts_refresh()
````

_NOTE: Presently all fact retrieval functions are defined in the `facts` directory of this module.  In future versions of this code, you will be able to add your own facts in arbitrary locations._

### Resource Abstrations

The following code example illustrates how to use the SRX "ZoneAddrBook" resource to add a new address item to a zone's address book.

````python
from pprint import pprint

from jnpr.eznc import Netconf
from jnpr.eznc.resrc.srx import ZoneAddrBook

jdev = Netconf(user='jeremy', host='vsrx_cyan', password='jeremy1')
jdev.open()

# bind a ZoneAddrBook resource manager to this Netconf instance.
# you get to chose the attribute name, in this example, we will
# use the attribute 'ab'.

jdev.bind( ab=ZoneAddrBook )

# now select the address book for a specific security zone
# this will load the contents of the address book from the
# Junos SRX device

trust_ab = jdev.ab["TRUST"]

# an address book manages two resources, the list of address 
# items, and the list of address-sets.  You can see what 
# a specific resource manages by looking at the :manages:
# property

pprint( trust_ab.manages )
#>>> ['addr', 'set']

# lets add a new address item called 'JEREMY-HOST' with
# and IP address of '192.168.1.1'

jeremy = trust_ab.addr['JEREMY-HOST']

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

For more details on using the Utilities, see [here](docs/INTRO_UTILS.md).

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

# EXCEPTION HANDLING

This module defines a set of Exceptions, and these are defined in the `exceptions.py` file.  The general use-case looks something like this:
````python
try:
   jdev.rpc.i_did_something_goofy()
except Exception as err:
   # err has attributes you can look at to coorelate the command (cmd)
   # and response (rsp).  Both of these are lxml Elements.  So here
   # is an example of just dumping the error to the screen
   
   etree.dump( err.rsp )
````

There are specific Exceptions for configuration changes: locking, loading changes, unlocking, and commiting.  

For more details on exceptions, see [here](docs/EXCEPTIONS.md).


# DEPENDENCIES

This module requires Python 2.7.  

  * [lxml](http://lxml.de/index.html) - XML programming library
  * [ncclient](https://github.com/juniper/ncclient) (_Juniper edition_) - NETCONF base library
  * [paramiko](https://github.com/paramiko/paramiko) - SSH library (also used by ncclient)
  * [scp](https://github.com/jbardin/scp.py) - SCP library
  * [jinja2](http://jinja.pocoo.org/docs) - templating library
  * [netaddr](https://pypi.python.org/pypi/netaddr/) - Network IPv4,IPv6 address library

# LICENSE

  BSD-2
  
# CONTRIBUTORS

  - Jeremy Schulman, @nwkautomaniac
