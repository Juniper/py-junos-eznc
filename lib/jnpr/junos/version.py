VERSION = "2.6.4"
DATE = "2022-Jun-9"

# Augment with the internal version if present
try:
    from ._version import get_versions

    VERSION = get_versions()["version"]
    del get_versions
except ImportError:
    # No internal version
    pass
