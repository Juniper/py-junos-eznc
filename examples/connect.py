import re
from pprint import pprint as pprint
import paramiko
import os, sys

import jnpr.junos as junos

if len(sys.argv) < 3:
  print "you must provide a Junos user and target hostname"
  sys.exit(1)

# going to use paramiko SSHConfig to retrieve the port parameters for a given
# host.  Doing this because I tend to use jumphosts to get to devices behind
# firewalls/etc.  This is a pretty useful technique to illustrate:

user_name = sys.argv[1]
junos_hostname = sys.argv[2]
config_file = os.path.join(os.getenv('HOME'),'.ssh/config')
ssh_config = paramiko.SSHConfig()
ssh_config.parse(open(config_file,'r'))
got_lkup = ssh_config.lookup( junos_hostname )

from getpass import getpass

login = dict(
  host=got_lkup['hostname'],
  port=got_lkup.get('port',830),
  user=user_name, password=getpass()
)

dev = junos.Device(**login).open()

