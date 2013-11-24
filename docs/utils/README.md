## Using Utility Libraries

Utilities are collections of routines that serve a common purpose.  The collection of utilities in _Junos EZ_ is expected to grow over time.  Some of the Utilities to date include, but are not limited to:

* Config - commonm configuration tasks
* SCP - secure file copy
* SW - softawre upgrade
* FS - filesystem utils

A Utility library is a Widget in the _Junos EZ_, so associating one to a _Device_ variable is the same process as described [here](../device.md).

Each Utility library should be fully documented, so you can use the Python help() routine.

Here is an example to check the Junos candidate configuraiton for any uncommitted changes.
````python
>>> from jnpr.junos.utils.config import Config

>>> cu = Config(dev)
>>> cu.pdiff()

[edit system login]
!     inactive: user jeremy { ... }
[edit system login user jeremy]
-    full-name "Jeremy L. Schulman";
+    full-name "Jeremy Schulman";
-    uid 2001;
+    uid 3000;
````
Then we could check to see if the commit passes "commit check":
````python
>>> cu.commit_check()
True
````

But maybe we want to discard these changes; i.e. "rollback":
````python
>>> cu.rollback()
True
>>> cu.pdiff()
None
````


