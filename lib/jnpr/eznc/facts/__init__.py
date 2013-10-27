from .chassis import chassis
from .routing_engines import routing_engines

FACT_LIST = [
  chassis,
  routing_engines
]

__all__ = ['FACT_LIST']