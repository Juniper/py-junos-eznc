import pdb

from exampleutils import *
from junos.eznc import Netconf as Junos
from junos.eznc.resources.srx import Application

from lxml.builder import E 
from lxml import etree

login = dict(user='jeremy', host='vsrx_cyan', password='jeremy1')

jdev = Junos(**login)

jdev.open()

apps = Application( jdev )



