import pdb
from pprint import pprint as pp 
from lxml.builder import E 
from lxml import etree

# junos "ez" module
from jnpr.eznc import Netconf
from jnpr.eznc.utils import *
from jnpr.eznc.resources.srx import *

dev = Netconf(user='jeremy', host='jnpr-dc-fw').open()

## now play around with jdev object ...
## when done, you should issue dev.close()
