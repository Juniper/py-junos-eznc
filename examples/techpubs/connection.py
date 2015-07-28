from jnpr.junos import Device
import sys

dev = Device('router1.example.com', user='root')
try:
    dev.open()
except Exception as err:
    print "Unable to connect to host:", err
    sys.exit(1)

print dev.facts
dev.close()
