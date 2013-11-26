import sys
from pprint import pprint as pp
import jnpr.junos as junos

if len(sys.argv) < 3:
  # argv[1] = user-name
  # argv[2] = host-name
  print "you must provide a Junos user and target hostname"
  sys.exit(1)

def sshconf_find(host):
  import os, paramiko

  # going to use paramiko SSHConfig to retrieve the port parameters for a given
  # host.  Doing this because I tend to use jumphosts to get to devices behind
  # firewalls/etc.  This is a pretty useful technique to illustrate:
  config_file = os.path.join(os.getenv('HOME'),'.ssh/config')
  ssh_config = paramiko.SSHConfig()
  ssh_config.parse(open(config_file,'r'))
  return ssh_config.lookup( host )

def connect(user, host):
  from getpass import getpass  
  got_lkup = sshconf_find( host )
  login = dict(
    host=got_lkup['hostname'],
    port=got_lkup.get('port',830),
    user=user, password=getpass()
  )
  return junos.Device(**login).open()

dev = connect(sys.argv[1], sys.argv[2])

