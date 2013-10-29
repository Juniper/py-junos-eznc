# for debugging ...
import pdb
from pprint import pprint as pp 
from lxml import etree

# for the example ...
from jnpr.eznc import Netconf 
from jnpr.eznc.resources.srx.nat import NatSrcRuleSet
from jnpr.eznc.utils import Config

jdev = Netconf(user='jeremy', host='vsrx_cyan', password='jeremy1')
jdev.open()

cu = Config(jdev)
r_mgr = NatSrcRuleSet(jdev)

rset = r_mgr["outside"]
rset['zone_from'] = 'UNTRUST'
rset['zone_to'] = 'TRUST'
rset.write()

print cu.diff()
# [edit security]
# +   nat {
# +       source {
# +           rule-set outside {
# +               from zone UNTRUST;
# +               to zone TRUST;
# +           }
# +       }
# +   }

print "rollback..."
cu.rollback()



