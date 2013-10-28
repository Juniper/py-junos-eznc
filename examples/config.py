import pdb
from pprint import pprint as pp 
from lxml import etree
from lxml.builder import E 

# for the example ...
from exampleutils import *
from jnpr.eznc import Netconf as Junos
from jnpr.eznc.utils import ConfigUtils

# create a junos device and open a connection

login = dict(user='jeremy', host='vsrx_cyan', password='jeremy1')
jdev = Junos(**login)
jdev.open()

jdev.bind( cu=ConfigUtils )

# make changes using the 'set' style

print "Making changes using 'set' style ... "
set_commands = """
set system host-name jeremy
set system domain-name jeremy.com
"""

rsp = jdev.cu.load( set_commands, format='set' )

def show_diff_and_rollback():
  # dump the diff:
  print jdev.cu.diff()
  # [edit system]
  # -  host-name jnpr-dc-fw;
  # +  host-name jeremy;
  # +  domain-name jeremy.com;

  print "Rolling back...."
  jdev.cu.rollback()

show_diff_and_rollback()

print "Making changes using 'curly-text' style ..."

# make changes using the 'text-curly' style
conf_change = """
system {
  host-name jeremy;
  domain-name jeremy.com;
}
"""

rsp = jdev.cu.load( conf_change, format='text')
show_diff_and_rollback()
