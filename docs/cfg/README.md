# Configuration Resources

A _Resource_ is a structured approach for making Junos configuration change without requiring specific knowledge of the underlying Junos/XML.  Each _Resource_ is defined by a unique name-identifier, and a collection of property values you can read/write.

For example, consider managing the authorized login users on a Junos device.  From the Junos CLI:

    [edit system login user <name>]  

Each login user has a unique name and a collection of property values, such as class, uid, full-name, etc.  

Let's say I wanted to access the user "jeremy".  Here is brief example with _Junos EZ_ using the _User_ Resource; assume that _dev_ is a connected _Device_ variable.

````python
# import the User resource
>>> from jnpr.junos.cfg.user import User

# access the login user 'jeremy' from this device
>>> me = Users(dev, 'jeremy')

# now show some of the User properties
>>> me.fullname
'Jeremy L. Schulman'
>>> me.userclass
'super-user'
````
There are a few different ways to access a resource.  The first way, as illustrated above, is to directly request a resource specifically by device.  The second way is *not* to provide a unique name (like 'jeremy').  In doing this, you create a _Resource Manager_.  A Resource Manager allows you to then access a specific resource by name.  The benefit of using a Resource Manager is that you can obtain a list of resource names as well as their catalog of properites.  This makes it very handy to quickly examnine what exists in the Junos configuration.

## Resource Managers

### Accessing a Resource Manager

To bind a resource manager to a Netconf instance, you use the Netconf.bind() method.  To use the ZoneAddrBook, resource, for example, you would create a resource manager as follows:

````python
from jnpr.eznc.cfg.srx import ZoneAddrBook

jdev.bind( ab=ZoneAddrBook )
````

The `bind` method takes a key/value pair - the key is the name of the attribute you want to bind to the Netconf instance (so you get to pick the name) and the value is the class of the Resource, in this example `ZoneAddrBook`.  

Every resource has a name.  For the case of the ZoneAddrBook, the name is the security zone name.  So if we want to select the address-book for the zone called "TRUST", we would do the following:

````python
trust_ab = jdev.ab["TRUST"]
````

Selecting a resource is make by using the `[<name>]` mechanism.  This returns a specific resource, in this case the address-book for the TRUST zone.

### Resource Manager Properties

All resource managers maintain two properties: a list of names that it manages, and a catalog of those resources.  The list is a Python list, and the catalog is a Python dictionary where the key is a name of the resource and the value is a dictorany of resource properties.  This list and catalog is retrieved by accessing the attributes as properties:

````python
## pretty-print the list of address-book items; this would actually print a list of security zone names

pprint( jdev.ab.list )

## pretty-print the catalog of address-books; this would effectively dump all address-book information
## in dictionary format.

pprint( jdev.ab.catalog )
````
Once you've accessed either `list` or `catalog` the values are cached.  If you need to refresh these properties you can explicity refresh the list or the catalog, or both, as illustrated:

````python
# selectively refresh

jdev.ab.list_refresh()
jdev.ab.catalog_refresh()

# or refresh both

jdev.ab.refresh()
````

## Resources

There are two ways to access a resource.  The common way is by using a resource-manager, and selecting the resource by name using the `[<name>]` mechanism, as previous illustrated.  

Alternatively, you can select a specific resource without using a manager by directly instantiating the resource.  For example, selecting the "TRUST" zone directly, you would do the following:

````python
from jnpr.eznc import Netconf
from jnpr.eznc.cfg.srx import Zone

jdev = Netconf(user='jeremy',password='jeremy1',host='vsrx_cyan')
jdev.open()

trust_zone = Zone(jdev, "TRUST")

# now do things with the trust_zone instance ...
````

You manage the specific configuration elements of the resource by reading and writing "properties".  You access these properties using the `[<property-name>]` meachism.  For example, a Zone address-book item has a property called "ip_prefix".  You can read and write the value, as illustrated:

````python
# select the specific address resource called "JEREMY-HOST" in the "TRUST" zone

jeremy = jdev.ab["TRUST"].addr["JEREMY-HOST"]

# display the current value

print jeremy['ip_prefix']
#>>> '192.168.1.1/32'

# now change it to "192.168.100.1/32"
jeremy['ip_prefix'] = "192.168.100.1/32"

# write the change to the Junos device
jeremy.write()
````

Alternatively you can modify the resource properites using the _call_ mechanism, as illustrated:
````python
jeremy(ip_prefix="192.168.100.1/32", description="Jeremy laptop")
jeremy.write()
````

### Resource Attribute Properties

Each resource provides instance attribute properties:

  * name - the name of the resource
  * properties - a list of properties you can read/write
  * manages - a list of other resources managed by this resource 
  * exists - True/False if resource exists in Junos config
  * active - True/False if resource is active in Junos config
  * xml - The actual Junos XML associated with this resource (typically for debug)

The following are also properties that provide "short-cuts" to other objects:

  * N - the Junos Netconf object instance
  * M - the instance to the resource manager
  * P - the instance to the resource parent
  * R - the RPC metaexec instance

### Resource Methods

You can use the following methods on any resource.  These methods will read/write the Junos device, but changes are not committed.  You must explicity commit changes, typically by the ConfigUtils library.

  * read() - reads the resource config from the Junos device
  * write() - writes the modified resource properties to the Junos device
  * delete() - removes the resource from the Junos config
  * rename() - renames the resource in the Junos config
  * activate() - activates the resource in the Junos config
  * deactivate() - deactivates the resource in the Junos config
  * reorder() - changes the ordering of the resource in the Junos config

_NOTE: Each resource maitains separate read and write dictionary caches.  When you invoke the `read()` method, the Junos device is read and the read-cache is loaded.  When you modify the resource properites using the `[<property-name>]` mechaism, you are storing values into the write-cache, but not directly to the device.  You write back to the Junos device using the `write()` method.  In this way you can update many resource properties with a single `write()`_



