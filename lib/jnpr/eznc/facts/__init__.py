from .chassis import chassis
from .routing_engines import routing_engines
from .personality import personality

FACT_LIST = [
  chassis,
  routing_engines,
  personality
]

__all__ = ['FACT_LIST']