"""
Junos PyEZ Utility Base Class
"""


class Util(object):
    """
    Base class for all utility classes
    """

    def __init__(self, dev):
        self._dev = dev

    def __repr__(self):
        return "jnpr.junos.utils.%s(%s)" % (self.__class__.__name__, self._dev.hostname)

    # -------------------------------------------------------------------------
    # property: dev
    # -------------------------------------------------------------------------

    @property
    def dev(self):
        """
        :returns: the Device object
        """
        return self._dev

    @dev.setter
    def dev(self, value):
        """read-only property"""
        raise RuntimeError("read-only: dev")

    # -------------------------------------------------------------------------
    # property: rpc
    # -------------------------------------------------------------------------

    @property
    def rpc(self):
        """
        :returns: Device RPC meta object
        """
        return self._dev.rpc

    @rpc.setter
    def rpc(self, value):
        """read-only property"""
        raise RuntimeError("read-only: rpc")
