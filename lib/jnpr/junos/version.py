VERSION = "2.7.4.dev0"
DATE = "2025-Feb-28"

# Augment with the internal version if present
try:
    from ._version import get_versions

    VERSION = get_versions()["version"]
    del get_versions
except ImportError:
    # No internal version
    pass
