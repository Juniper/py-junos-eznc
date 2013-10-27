# Using Utility Libraries

## ConfigUtils

A collection of functions to facilitate configuration change management.  The following functions are provided as part of this library:

````python
from jnpr.eznc.utils import ConfigUtils
````

  * commit() - performs a commit of the candidate configuration
  * commit_check() - performs a commit "check" of the candidate configuration
  * diff() - returns a diff string of the candidate configuration; i.e. "show | compare ..."
  * lock() - attempt an exclusive lock on the candidate configuration
  * rollback() - performs the rollback operation
  * unlock() - attempt to unlock the candidate configuration
  
## REUtils

A collection of functions for handling the routing-engine (control-CPU).  

___WORK IN PROGRESS - NOT YET AVAILABLE___

## FileSystemUtils

A collection of functions for handling file-system operations, like MD5 checksum, copying, storage usage/cleanup.

___WORK IN PROGRESS - NOT YET AVAIALBLE___
