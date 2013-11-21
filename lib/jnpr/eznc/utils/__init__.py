from .util import Util

# @@@ may remove these and have folks import the specific files directly, TBD

import warnings

warnings.warn("util imports [Config,FS,SCP] will be removed in 0.0.3", DeprecationWarning)

from .config import Config
from .fs import FS
from .scp import SCP
