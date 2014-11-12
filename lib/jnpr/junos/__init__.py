from jnpr.junos.device import Device
from jnpr.junos.factory.to_json import PyEzJSONEncoder
from jnpr.junos.facts.swver import version_info, version_yaml_representer
from . import jxml
from . import jxml as JXML
from . import version
from . import exception

import json
import yaml

__version__ = version.VERSION
__date__ = version.DATE

#import time
#__date__ = time.strftime("%Y-%b-%d")

# Set default JSON encoder
json._default_encoder = PyEzJSONEncoder()

# Disable ignore_aliases for YAML dumper
# To support version_info
yaml.dumper.SafeDumper.ignore_aliases = lambda self, data: True
yaml.dumper.Dumper.ignore_aliases = lambda self, data: True
# Add YAML representer for version_info
yaml.Dumper.add_multi_representer(version_info, version_yaml_representer)
yaml.SafeDumper.add_multi_representer(version_info, version_yaml_representer)
