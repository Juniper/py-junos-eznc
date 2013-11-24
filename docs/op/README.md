## Getting Operational / Run-State Data

Operational, or "run-state", data refers not to the configuration of the device, but rather the status of information.  From the Junos CLI, this information is obtained using "show" commands, like "show interfaces".  Gathering operaitonal information is a critical function of automating network infrastrcutre.  The _Junos EZ_ library provides two abstractions to facilitate getting this data: _Tables_ and _Views_.

#### Tables

The concept of a table is nothing new, taking it from the world of databses.  So if you think of the Junos OS having a "Operational Database", then that database contains a collection of tables.  For example the "show route" command could provide the route _table_ and "show interfaces media [fgx]e*" could provide the Ethernet port _table_.

Each table has a collection of items (database 'records').  The item data can be examined as a _View_.

#### Views

Think of a view the same way you would think of the Junos CLI options "brief","terse","detail","extensive".  The underlying data (table record) that Junos provides is the same.  The Junos CLI simply applies a different "view" to that data and renders the data in human readable form (aka. "CLI output").
