from jnpr.junos.facts.chassis import facts_chassis
from jnpr.junos.facts.routing_engines import facts_routing_engines
from jnpr.junos.facts.personality import facts_personality
from jnpr.junos.facts.swver import facts_software_version
from jnpr.junos.facts.ifd_style import facts_ifd_style
from jnpr.junos.facts.switch_style import facts_switch_style
from jnpr.junos.facts.session import facts_session
from jnpr.junos.facts.srx_cluster import facts_srx_cluster
from jnpr.junos.facts.domain import facts_domain

FACT_LIST = [
    facts_chassis,                  # first
    facts_routing_engines,          # second
    facts_personality,              # third
    facts_srx_cluster,              # four
    facts_software_version,         # fifth

    facts_domain,
    facts_ifd_style,
    facts_switch_style,
    facts_session
]

__all__ = ['FACT_LIST']
