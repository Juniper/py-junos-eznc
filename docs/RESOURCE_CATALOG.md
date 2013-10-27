# Catalog of Supported Resources

### SRX

The first pass of this module is targeting resource abstractions for the SRX firewall products.  These resource abstractions include:

 * Security zone interfaces
 * Security zone address-book items and sets
 * Security policy contexts and rule-sets
 * Security screens
 * Security application items and sets
 * Source NAT address pools, rule-sets, and rules
 * Static NAT rule-sets and rules

````python
from jnpr.eznc.resources.srx import Zone, ZoneAddrBook
from jnpr.eznc.resources.srx import ZoneAddrFinder
````
The Zone resource manages interfaces and the address-book.  The ZoneAddrFinder object does not manage resources, but it is associated here since locating address-book entries is a common congruent task.

````python
from jnpr.eznc.resources.srx import PolicyContext
````
The PolicyContext resource manages security policy rules

````python
from jnpr.eznc.resources.srx import Application, ApplicationSet
````
The Application and ApplicationSet resources manage the applicaiton definitions used by security policies

````python
from jnpr.eznc.resources.srx.nat import NatSrcPool, NatSrcRuleSet, NatSrcRule
````
These resources manage aspects of source-NAT configuration
