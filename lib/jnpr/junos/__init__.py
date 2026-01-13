import json
import logging

import yaml
from jnpr.junos.console import Console
from jnpr.junos.device import Device
from jnpr.junos.factory.to_json import PyEzJSONEncoder
from jnpr.junos.facts.swver import version_info, version_yaml_representer

from . import exception
from . import jxml
from . import jxml as JXML
from . import version

__date__ = version.DATE

# import time
# __date__ = time.strftime("%Y-%b-%d")

# Set default JSON encoder
setattr(json, "_default_encoder", PyEzJSONEncoder())

# Disable ignore_aliases for YAML dumper
# To support version_info
yaml.dumper.SafeDumper.ignore_aliases = lambda self, data: True
yaml.dumper.Dumper.ignore_aliases = lambda self, data: True
# Add YAML representer for version_info
yaml.Dumper.add_multi_representer(version_info, version_yaml_representer)
yaml.SafeDumper.add_multi_representer(version_info, version_yaml_representer)


# Suppress Paramiko logger warnings
plog = logging.getLogger("paramiko")
if not plog.handlers:

    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

    plog.addHandler(NullHandler())

from ._version import get_versions

__version__ = get_versions()["version"]
del get_versions

from . import _version

__version__ = _version.get_versions()["version"]
