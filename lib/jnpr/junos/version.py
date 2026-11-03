VERSION = "2.8.3"
DATE = "2026-Nov-3"

# Augment with the internal version if present
try:
    from ._version import get_versions

    VERSION = get_versions()["version"]
    del get_versions
except ImportError:
    # No internal version
    pass
