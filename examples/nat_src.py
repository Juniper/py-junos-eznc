import pdb

from pprint import pprint as pp 

from exampleutils import *
from jnpr.eznc import Netconf as Junos
from jnpr.eznc.resources.srx import NatSimpleSource
from jnpr.eznc.utils import ConfigUtils
from jnpr.eznc.exception import *

from lxml.builder import E 
from lxml import etree

login = dict(user='jeremy', host='vsrx_cyan', password='jeremy1')

jdev = Junos(**login)
jdev.open()

jdev.ez( cu=ConfigUtils )     # jdev.ez.cu.<...>

r = NatSimpleSource( jdev, "outbound-all")

r.read()
r['match_src_addr'] = '1.1.1.1'





