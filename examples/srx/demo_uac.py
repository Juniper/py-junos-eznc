import re
from pprint import pprint as pprint

from jnpr.eznc import Netconf

# local import
from uac import UAC

dev = Netconf(user='jeremy',host='localhost',port=9002)
dev.open()

dev.bind(uac=UAC)
dev.uac.get_users()

print dev.uac.user_names
