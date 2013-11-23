import re
from pprint import pprint as pprint
import paramiko
import os, sys

from jnpr.junos import Device as Netconf

# local import
from uac import UAC

if len(sys.argv) < 2:
  print "you must provide a Junos target hostname"
  sys.exit(1)

# going to use paramiko SSHConfig to retrieve the port parameters for a given
# host.  Doing this because I tend to use jumphosts to get to devices behind
# firewalls/etc.  This is a pretty useful technique to illustrate:

junos_hostname = sys.argv[1]
config_file = os.path.join(os.getenv('HOME'),'.ssh/config')
ssh_config = paramiko.SSHConfig()
ssh_config.parse(open(config_file,'r'))
got_lkup = ssh_config.lookup( junos_hostname )

dev = Netconf(user='jeremy',host=got_lkup['hostname'],port=got_lkup['port'])
dev.open()

dev.bind(uac=UAC)
dev.uac.get_users()

print "UAC users:"
print dev.uac.usernames
