VERSION = "2.6.6.dev0"
DATE = "2022-July-30"

# Augment with the internal version if present
try:
    from ._version import get_versions

    VERSION = get_versions()["version"]
    del get_versions
except ImportError:
    # No internal version
    pass
