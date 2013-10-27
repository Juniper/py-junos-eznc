from .chassis import chassis
from .routing_engines import routing_engines
from .personality import personality
from .swver import software_version
from .ifd_style import ifd_style
from .switch_style import switch_style

FACT_LIST = [
  chassis,
  routing_engines,
  personality,
  software_version,
  ifd_style,
  switch_style,
]

__all__ = ['FACT_LIST']