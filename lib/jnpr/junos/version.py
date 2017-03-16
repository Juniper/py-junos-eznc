VERSION = "2.1.dev0"
DATE = "2017-Mar-16"
AUTHOR = "Jeremy Schulman, Nitin Kumar, Rick Sherman, Stacy Smith"

# Augment with the internal version if present
try:
    from jnpr.junos.internal_version import INTERNAL_VERSION
    VERSION += '+internal.' + str(INTERNAL_VERSION)
except ImportError:
    # No internal version
    pass
