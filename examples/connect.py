import sys
from pprint import pprint as pp
import jnpr.junos as junos
from os import getenv

def connect(host, user, password=None):
  from getpass import getpass
  if password is None: password = getpass('password: ')
  return junos.Device(host, user=user, password=password).open()

if len(sys.argv) > 1:
  dev = connect(sys.argv[2], sys.argv[1])

