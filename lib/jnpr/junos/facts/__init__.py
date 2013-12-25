from .chassis import chassis
from .routing_engines import routing_engines
from .personality import personality
from .swver import software_version
from .ifd_style import ifd_style
from .switch_style import switch_style
from .session import *
from .srx_cluster import srx_cluster

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