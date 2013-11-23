# Exceptions

Specific Exception names are imported as shown:
```python
from jnpr.eznc.exception import *
````

The following Exceptions are defined:
  * RpcError - general RPC error
  * CommitError - resulting for issuing a commit operation
  * LockError - resulting from issuing a lock-configuration operation
  * UnlockError - resulting from issuing an unlock-configuration command

All exceptions provide the following property attributes:
  * cmd - XML RPC command, lxml Element
  * rsp - XML RPC response, lxml Element

Generally speaking, if you have any doubt that an RPC will excecute properly, you should trap the exception.  YOu can either use the explicit RpcError exception or the generic Exception (shown):
````python
try:
   jdev.rpc.do_something_goofy(var1="dude")  # will result in RpcError exception
except Exception as err:
   # now you can access err as an RpcError
   print "CMD:"
   etree.dump(err.cmd)
   print "RSP:"
   etree.dump(err.rsp)
   
# results in the following output:
# CMD:
# <do-something-goofy xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
#   <var1>dude</var1>
# </do-something-goofy>
# RSP:
# <rpc-error xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" 
#   mlns:junos="http://xml.juniper.net/junos/12.1X44/junos" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
# <error-severity>error</error-severity>
# <error-info>
# <bad-element>do-something-goofy</bad-element>
# </error-info>
# <error-message>syntax error</error-message>
# </rpc-error>
````

The CommitError, LockError, and UnlockError inherit from RpcError, and are *only* raised when you use the Config utilties.  If you perform a native RPC command directly, you will not get one of these Exceptions, but rather an exception from the underlying NETCONF transport module (ncclient as of now).

For example:

```python
from jnpr.eznc import Netconf
from jnpr.eznc.utils import Config
from jnpr.eznc.exception import *

# assume :jdev: is an open Netconf instance

jdev.bind(cu=Config)

# assume that someone else has the exclusive configuration lock.
# the following will cause a LockError

jdev.cu.lock()
#>>> jnpr.eznc.exception.LockError

# trying to do this with the native XML RPC results in an ncclient exception:

jdev.rpc.lock_configuration()
#>>> ncclient.operations.rpc.RPCError: 
#>>> Configuration database is already open
````
_NOTE: It is recommended that you use the Config utils rather than the native XML._



  
