# Using Resources

Resources provide abstrations on specific Junso configuration items without requiring specific knowledge of the underlying Junos/XML.  To access a resource you must bind a class of that resource to a Netconf instance, and this creates a "Resource Manager".

### Binding a Resource Manager

To use the ZoneAddrBook, resource, for example, you would create a resource manager as follows:

````python
from jnpr.eznc.resources.srx import ZoneAddrBook

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







