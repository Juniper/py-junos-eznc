## Device Connection

````python
from jnpr.junos import Device
````

### Basic Session Management

### Associating Widgets to a Device

We'll use the term _"widget"_ to refer to anything that we want to associated with a Device instance.  This could be a configuration _Resource_, a _Util_ library, a Operational data _Table_, or other items defined in the _Junos EZ_ library.

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

The benefit of using _Device.bind()_ is the associate a set of widgets with a Device, and then simply pass
that device around for later use.  This way you don't need to keep creating widget stand-alone variables.  You can get a list of managed widgets by examining the _Device.manages_ property:
````python
>>> dev.manages
['cu']
````
### Remote Procedure Call (RPC)


