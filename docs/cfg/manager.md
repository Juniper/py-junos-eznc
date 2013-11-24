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
#### Getting a List of Resource Names

You can get a list of Resource item names by accessing the _Resource.list_.
````python
>>> users.list
['jeremy', 'kim']
````

#### Getting the Catalog of Resources

You can get a catalog of Resource items by accessing the _Resource.catalog_.  A catalog is a Python dictionary where the key is the resource name and the value is the set of resource property values.
````python
>>> pprint(users.catalog)
{'jeremy': {'$password': '$1$n/RPB3fZ$RGPy8hymoTa8G5oGiJMdr.',
            '$sshkeys': [('ssh-rsa',
                          'ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAm2JAEXQ<snip>')],
            '_active': False,
            '_exists': True,
            'fullname': 'Jeremy Schulman',
            'uid': 3000,
            'userclass': 'super-user'},
 'kim': {'$password': 'WqaaliqOgnXZM',
         '$sshkeys': [('ssh-dsa',
                       'ssh-dss AAAAB3NzaC1kc3MAAACBAMr4aHSXUBBss9XiW6<snip>')],
         '_active': True,
         '_exists': True,
         'fullname': 'Kimmy Jones',
         'uid': 2004,
         'userclass': 'read-only'}}
````
Using the catalog is handy when looking for items.  For example, let's say you want to the list of user names if their userclass property is read-only.
````python
>>> [name for name in users.catalog if users.catalog[name]['userclass'] == 'read-only']
['kim']
````

#### Accessing a Specific Resource



