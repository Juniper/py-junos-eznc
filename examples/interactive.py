from junos_eznetconf import JunosEzNetconf as Junos
from lxml.builder import E 
from lxml import etree

def ppxml(r): print etree.tostring(r,pretty_print=True)

login = dict(user='jeremy', host='vsrx_cyan', password='jeremy1')

jdev = Junos(**login)



