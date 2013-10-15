import pdb

from pprint import pprint as pp 

from exampleutils import *
from junos.eznc import Netconf as Junos
from junos.eznc.resources.srx import ApplicationSet, PolicyContext
from junos.eznc.utils import ConfigUtils
from junos.eznc.exception import *

from lxml.builder import E 
from lxml import etree

login = dict(user='jeremy', host='vsrx_cyan', password='jeremy1')

jdev = Junos(**login)

jdev.open()

jdev.ez( cu=ConfigUtils )
jdev.ez( spc=PolicyContext )

pc = jdev.ez.spc[("PRODUCT-DC-ST1","PII-SOX-DC-ST1")]
r = pc.rule['105']
r['count'] = True





