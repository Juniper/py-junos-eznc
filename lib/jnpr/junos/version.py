VERSION = "2.2.1"
DATE = "2019-Apr-22"

# Augment with the internal version if present
try:
    from jnpr.junos.internal_version import INTERNAL_VERSION
    VERSION += '+internal.' + str(INTERNAL_VERSION)
except ImportError:
    # No internal version
    pass
