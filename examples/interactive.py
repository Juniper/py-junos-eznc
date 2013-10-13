import pdb

from exampleutils import *
from junos_eznetconf import JunosEzNetconf as Junos
from lxml.builder import E 
from lxml import etree

login = dict(user='jeremy', host='vsrx_cyan', password='jeremy1')

jdev = Junos(**login)

jdev.open()

def convert_me( junos, rpc_rsp_e, **kvargs ):
  pdb.set_trace()
  return rpc_rsp_e





