from jnpr.junos.facts.chassis import chassis
from jnpr.junos.facts.routing_engines import routing_engines
from jnpr.junos.facts.personality import personality
from jnpr.junos.facts.swver import software_version
from jnpr.junos.facts.ifd_style import ifd_style
from jnpr.junos.facts.switch_style import switch_style
from jnpr.junos.facts.session import *
from jnpr.junos.facts.srx_cluster import srx_cluster

FACT_LIST = [
    chassis,
    routing_engines,
    personality,
    srx_cluster,
    software_version,
    ifd_style,
    switch_style,
    session
]

__all__ = ['FACT_LIST']
