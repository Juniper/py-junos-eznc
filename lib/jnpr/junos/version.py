VERSION = "2.3.1"
DATE = "2019-Dec-10"

# Augment with the internal version if present
try:
    from jnpr.junos.internal_version import INTERNAL_VERSION
    VERSION += '+internal.' + str(INTERNAL_VERSION)
except ImportError:
    # No internal version
    pass
