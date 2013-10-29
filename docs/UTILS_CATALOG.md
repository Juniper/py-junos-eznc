# Catalog of Utilities

## Config

A collection of functions to facilitate configuration change management.  The following functions are provided as part of this library:

````python
from jnpr.eznc.utils import Config
````

  * commit() - performs a commit of the candidate configuration
  * commit_check() - performs a commit "check" of the candidate configuration
  * diff() - returns a diff string of the candidate configuration; i.e. "show | compare ..."
  * load() - lots of cool ways to load configuration into the device
  * lock() - attempt an exclusive lock on the candidate configuration
  * rollback() - performs the rollback operation
  * unlock() - attempt to unlock the candidate configuration
  
## RE

A collection of functions for handling the routing-engine (control-CPU).  

___WORK IN PROGRESS - NOT YET AVAILABLE___

## FS

A collection of functions for handling file-system operations, like MD5 checksum, copying, storage usage/cleanup.

___WORK IN PROGRESS - NOT YET AVAIALBLE___
