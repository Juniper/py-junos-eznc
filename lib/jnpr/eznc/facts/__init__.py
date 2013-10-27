from .chassis import chassis
from .routing_engines import routing_engines
from .personality import personality
from .swver import software_version

FACT_LIST = [
  chassis,
  routing_engines,
  personality,
  software_version,
]

__all__ = ['FACT_LIST']