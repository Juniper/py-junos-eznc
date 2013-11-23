### Device Connection

Each managed Junos device is modeled as a _jnpr.junos.Device_ variable (aka "instance").  The general process is you create a variable for each device, providing at least the host-name.  You can optionally provide a user-name (defaults to $USER) and a password (defaults to using ssh-keys).  You then open a connection to the device, perform automation activities on it, and finally close the connection.

Each managed Junos instance maintains a dictionary (hash-table) of "facts".  These facts are loaded when you open a connetion to the device.  Facts are generally static pieces of information, such as the software version or serial-number.  These facts form the basis for other modules when creating abstractions.  For example, configuring VLANs on one Junos product family, may actually be different from another, at the XML API devel.  The purpose of _Junos EZ_ is to abstract those differences so the user has a consistent automation interface.

* [Using Device](netconf.md)

### Getting Operational Data

Operational data, or sometimes called "Run-State" data, refers to the current running conditions of the device, and not its configuration.  For example, you may _configure_ an interface to use OSFP, but the neighbor connection status is operational data.  From the Junos CLI, operational data is displayed using "show" commands, e.g. _"show ospf neighbor"_.

_Junos EZ_ provides access to this information using two basic concepts: a "table" and a "view".  You can think of a "table" as the collection of data, and the "view" as the fields of specific data that you want to examine.  The _Junos EZ_ library will contain table and view definitions contributed by the community.  As as user/developer you can easily create your own tables and views.

* [Using Tables and Views](op/README.md)
* [Catalog of Tables](op/catalog.md)

### Managing Configuration

You can perform configuration changes in one of two ways: (1) structured Resources and (2) unstructured snippets.

Stuctured _Resources_ are defined as elements of the Junos configuration that you want to manage as discrete items.  For example, a SRX security zone has an address-book, that it turn contains a list of address items and a list of address-sets.  The purpose of the resource abstraction is to enable the user to manage these items as simple Python objects, and not requiring kownledge of the underlying Junos/XML.  Resources can be Junos product family specifc.  Security Zones, for example, would be found only on SRX products.

* [Using Resources](cfg/README.md)
* [Catalog of Resources](cfg/catalog.md)

Unstructued snippets are handed by the _Config_ utiilty library using the _load()_ routine. 

### Utility Libraries

An application will often want to perform common fucntions, and again wihtout requiring knowledge of the underlying Junos/XML.  The Config library, for example, allows you to do things like "rolllback", "commit check" and "show | compare" to get a diff-patch output of candidate changes.

* [Using Utilities](utils/README.md)
* [Catalog of Utilities](utils/catalog.md)

### RPC Metaprogramming 

You should always have the ability to "do anything" that the Junos/XML API provides.  This module attempts to make accessing Junos at this low-level "easy".  The term "metaprogramming" basically means that this module will dynamically create Junos XML Remote Procdure Calls (RPCs) as you invoke them from your program, rather that pre-coding them as part of the module distribution.  Said another way, if Junos provides thousands of RPCs, this module does *not* contain thousands of RPC functions.  It metaprogramms only the RPCs that you use, keeping the size of this module small, and the portability flexible.

* [Using RPC metaprogramming](docs/rpcmeta.md).

