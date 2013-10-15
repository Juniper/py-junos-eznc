import pdb

from exampleutils import *
from junos.eznc import Netconf as Junos
from junos.eznc.resources.srx import ApplicationSet
from junos.eznc.utils import ConfigUtils

from lxml.builder import E 
from lxml import etree

login = dict(user='jeremy', host='vsrx_cyan', password='jeremy1')

jdev = Junos(**login)

jdev.open()

jdev.ez( cu=ConfigUtils )
jdev.ez( aset=ApplicationSet )

r = jdev.ez.aset["JMET-DB-PORTS"]

