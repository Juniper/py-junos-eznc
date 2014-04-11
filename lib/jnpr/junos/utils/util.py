class Util(object):

    """ Base class for all utility classes """

    def __init__(self, dev):
        self._dev = dev

    def __repr__(self):
        return "jnpr.junos.utils.%s(%s)" % (
            self.__class__.__name__, self._dev.hostname)

    # -------------------------------------------------------------------------
    # property: dev
    # -------------------------------------------------------------------------

    @property
    def dev(self):
        """ return the Device device object """
        return self._dev

    @dev.setter
    def dev(self, value):
        raise RuntimeError("read-only: dev")

    # -------------------------------------------------------------------------
    # property: rpc
    # -------------------------------------------------------------------------

    @property
    def rpc(self):
        """ return the Device RPC meta object """
        return self._dev.rpc

    @rpc.setter
    def rpc(self, value):
        raise RuntimeError("read-only: rpc")
