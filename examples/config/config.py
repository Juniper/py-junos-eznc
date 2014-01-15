import pdb
from pprint import pprint as pp 
from lxml import etree
from lxml.builder import E 

# for the example ...
from jnpr.junos import Device 
from jnpr.junos.utils.config import Config

# create a junos device and open a connection

jdev = Device('192.168.10.41',user='jeremy',password='jeremy123')
jdev.open()

jdev.bind( cu=Config )

def show_diff_and_rollback():
  # dump the diff:
  print jdev.cu.diff()
  # [edit system]
  # -  host-name jnpr-dc-fw;
  # +  host-name jeremy;
  # +  domain-name jeremy.com;

  print "Rolling back...."
  jdev.cu.rollback()

set_commands = """
set system host-name jeremy
set system domain-name jeremy.com
"""

print "Making changes using 'set' style ... "
rsp = jdev.cu.load( set_commands, format='set' )
show_diff_and_rollback()

# make changes using the 'text-curly' style
conf_change = """
system {
  host-name jeremy;
  domain-name jeremy.com;
}
"""

print "Making changes using 'curly-text' style ..."
rsp = jdev.cu.load( conf_change, format='text')
show_diff_and_rollback()

print "Loading config from file ..."
# now load something from a file:
rsp = jdev.cu.load( path="config-example.conf" )
show_diff_and_rollback()

print "Loading from template file ..."
tvars = dict(host_name='jeremy', domain_name='jeremy.net')
rsp = jdev.cu.load( template_path="config-example-template.conf", template_vars=tvars )
show_diff_and_rollback()

print "Loading from Template ..."
template = jdev.Template('config-example-template.conf')
rsp = jdev.cu.load( template=template, template_vars=tvars )
show_diff_and_rollback()

print "Loading changes from XML file ..."
rsp = jdev.cu.load( path='config-example.xml' )
show_diff_and_rollback()


