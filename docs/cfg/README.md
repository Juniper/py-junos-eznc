## Structured Config Management

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

* [Using a Resource](resource.md)
* [Using a Resource Manager](manager.md)

