from jnpr.junos.device import Device
from jnpr.junos.console import Console
from jnpr.junos.factory.to_json import PyEzJSONEncoder
from jnpr.junos.facts.get_software_information import version_info
from jnpr.junos.facts.get_software_information import version_yaml_representer
from . import jxml
from . import jxml as JXML
from . import version
from . import exception

import json
import yaml
import logging

import sys
import warnings

if sys.version_info[:2] == (2, 6):
    warnings.warn(
        "Python 2.6 is no longer supported by the Python core team, please "
        "upgrade your Python. A future version of PyEZ will drop "
        "support for Python 2.6",
        DeprecationWarning
    )

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


# Suppress Paramiko logger warnings
plog = logging.getLogger('paramiko')
if not plog.handlers:
    class NullHandler(logging.Handler):

        def emit(self, record):
            pass

    plog.addHandler(NullHandler())
