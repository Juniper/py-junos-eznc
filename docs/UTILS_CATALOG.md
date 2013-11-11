# Catalog of Utilities

## Config

A collection of functions to facilitate configuration change management.  The following functions are provided as part of this library:

````python
from jnpr.eznc.utils import Config
````
For more details you can either do a `help(Config)` or see the source code [here](https://github.com/jeremyschulman/py-junos-eznc/blob/master/lib/jnpr/eznc/utils/config.py).

## FS

A collection of functions for handling file-system operations, like MD5 checksum, copying, storage usage/cleanup.

````python
from jnpr.eznc.utils import FS
````
For more details you can either do a `help(FS)` or see the source code [here](https://github.com/jeremyschulman/py-junos-eznc/blob/master/lib/jnpr/eznc/utils/filesys.py).

## SCP

A utility object that *wraps* the [scp](https://github.com/jbardin/scp.py) object within a Netconf instance.  The SCP object can
be used as a context manager as well.

````python
from jnpr.eznc.utils import SCP
````
For more details you can either do a `help(SCP)` or see the source code [here](https://github.com/jeremyschulman/py-junos-eznc/blob/master/lib/jnpr/eznc/utils/ncscp.py). 

THere is also a demo illustrating the usage [here](https://github.com/jeremyschulman/py-junos-eznc/blob/master/examples/demo_scp.py).

## RE

A collection of functions for handling the routing-engine (control-CPU).  

___WORK IN PROGRESS - NOT YET AVAILABLE___
