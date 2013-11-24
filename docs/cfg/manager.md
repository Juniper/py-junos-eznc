## Resource Managers

Creating a Resource Manager is a similar process as a Resource Item, simply just don't provide a name.

````python
>>> from jnpr.junos.cfg.user import User

>>> users = User(dev)
>>> users
Resource Manager: User
````
Alteratively you can use the _Device.bind_ to attach the manager widget, as described [here](../device.md#associating-widgets-to-a-device).
````python
>>> dev.bind(users=User)
>>> dev.users
Resource Manager: User
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

