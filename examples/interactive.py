import pdb
from pprint import pprint as pp 
from lxml.builder import E 
from lxml import etree

# junos "ez" module
from jnpr.eznc import Netconf
from jnpr.eznc.exception import *

jdev = Netconf(user='jeremy', host='localhost', port=9001)
jdev.open()

## now play around with jdev object ...






