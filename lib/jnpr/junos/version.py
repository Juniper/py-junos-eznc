VERSION = "2.7.6.dev0"
DATE = "2025-Sep-23"

# Augment with the internal version if present
try:
    from ._version import get_versions

    VERSION = get_versions()["version"]
    del get_versions
except ImportError:
    # No internal version
    pass
