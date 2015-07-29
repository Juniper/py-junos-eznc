import sys
from jnpr.junos import Device
from jnpr.junos.exception import ConnectError


dev = Device('router1.example.com', user='root')
try:
    dev.open()
except ConnectError as err:
    print "Cannot connect to device: {0}".format(err)
    sys.exit(1)

print dev.facts
dev.close()
