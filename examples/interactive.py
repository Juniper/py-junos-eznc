import pdb
from pprint import pprint as pp 
from lxml.builder import E 
from lxml import etree
from exampleutils import *

# junos "ez" module
from jnpr.eznc import Netconf as Junos
from jnpr.eznc.exception import *

login = dict(user='jeremy', host='vsrx_cyan', password='jeremy1')

jdev = Junos(**login)
jdev.open()

from jnpr.eznc.utils import ConfigUtils
from jnpr.eznc.resources.srx import Zone, ZoneAddrBook, PolicyContext

## now play around with jdev object ...






