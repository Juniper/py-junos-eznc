import pdb

from exampleutils import *
import junos_eznetconf as junos
from junos_eznetconf import EzNetconf as Junos
from lxml.builder import E 
from lxml import etree

login = dict(user='jeremy', host='vsrx_cyan', password='jeremy1')

jdev = Junos(**login)

jdev.open()






