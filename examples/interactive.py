import pdb
from pprint import pprint as pp
from lxml.builder import E
from lxml import etree

# junos "ez" module
from jnpr.eznc import Netconf

dev = Netconf(user='jeremy', host='jnpr-dc-fw').open()

## now play around with dev object ...
## when done, you should issue dev.close()

