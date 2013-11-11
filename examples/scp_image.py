import pdb
from pprint import pprint as pp
from lxml.builder import E
from lxml import etree

# junos "ez" module
from jnpr.eznc import Netconf
from jnpr.eznc.utils import SCP

dev = Netconf(user='jeremy', host='jnpr-dc-fw').open()

## now play around with dev object ...
## when done, you should issue dev.close()

##### -----------------------------------------------
##### approach #1 - using 'bind' and directly open,
##### use, close the scp object
##### -----------------------------------------------

dev.bind(scp=SCP)

scp = dev.scp.open()

# scp file from server to Junos device
scp.put('jinstall.tgz','/var/tmp')

scp.close()

##### -----------------------------------------------
##### approach #2 - using context manager
##### -----------------------------------------------

# copy a file from the Junos device onto the server
with SCP(dev) as scp:
  scp.get('addrbook.conf')

dev.close()