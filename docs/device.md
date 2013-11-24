## Device Connection

````python
from jnpr.junos import Device
````
For complete documentation, you can use the Python shell `help(Device)`

### Opening a Connection

To create a _Device_ variable you must provide at least the target host-name.  You can optionally provide the user name, and if omitted will default to the _$USER_ environment value.  You can optinally provide a password, and if omitted will assume that ssh-keys are active.  The following code illustrates 3 ways to access the same device.

````python
from jnpr.junos import Device

dev = Device('jnpr-dc-fw')                          
dev = Device('jnpr-dc-fw', user='jeremy')           
dev = Device('jnpr-dc-fw', user='jeremy', password='logmein')
````

Once you've created the Device, you then open a connection:
````python
dev.open()
````

If an error occurs in the proces, an Exception will be raised.  

You can _call-chain_ the Device create and connection open together:
````python
dev = Device('jnpr-dc-fw').open()
````

#### Changing the RPC timeout

The default timeout for an RPC to transaction is 30 seconds.  You may need to change this value for long running requests.  Specifically if you perform a software-upgrade you *MUST* change this value.  You can read/write the timeout value as a Device property:

````python
# read the value
>>> dev.timeout
30

# change the value to 10 minutes
>>> dev.timeout = 10*60
````
### Closing a Device Connection

You should explicity close the Device connection when you are done, as a matter of proper "hygenine".
````python
dev.close()
````

### Associating Widgets to a Device

We'll use the term _"widget"_ to refer to anything that we want associated with a Device variable.  This could be a configuration Resource, a Utility library, a Operational data Table, or other items defined in the _Junos EZ_ library.

There are two ways you can associated a widget with a Device: (1) as a standalone variable, or (2) as a bound property.

For example, the follow two code snippets are effecitvely the same:

#### As a standalone variable:
````python
from jnpr.junos import Device
from jnpr.junos.utils.config import Config

dev = Device('jnpr-dc-fw').open()
cu = Config(dev)

# print the config diff
cu.pdiff()
````

#### Binding a property to the Device variable:
````python
from jnpr.junos import Device
from jnpr.junos.utils.config import Config

dev = Device('jnpr-dc-fw').open()
dev.bind(cu=Config)

# print the config diff
dev.cu.pdiff()
````

The benefit of using _Device.bind()_ is to associate a set of widgets with a Device, and then simply pass
that device around for later use.  This way you don't need to keep creating widgets stand-alone variables.  You can get a list of managed widgets by examining the _Device.manages_ property:
````python
>>> dev.manages
['cu']
````
### Remote Procedure Call (RPC)

At times you may want to directly access the Junos XML API command/respnse.  Use the _Device.rpc_ meta-programming object to execute an RPC and return back the XML response.  

* [Using RPC](rpcmeta.md)
