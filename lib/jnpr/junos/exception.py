from lxml import etree
from jnpr.junos import jxml


class RpcError(Exception):

    def __init__(self, cmd=None, rsp=None, errs=None):
        """
          :cmd: is the rpc command
          :rsp: is the rpc response (after <rpc-reply>)
          :errs: is a list of <rpc-error> elements
        """
        self.cmd = cmd
        self.rsp = rsp
        self.errs = errs

    def __repr__(self):
        """
          pprints the response XML attribute
        """
        if None != self.rsp:
            return etree.tostring(self.rsp, pretty_print=True)


class CommitError(RpcError):

    def __init__(self, cmd=None, rsp=None, errs=None):
        RpcError.__init__(self, cmd, rsp, errs)
        self.rpc_error = jxml.rpc_error(rsp)


class LockError(RpcError):

    def __init__(self, rsp):
        RpcError.__init__(self, rsp=rsp)
        self.rpc_error = jxml.rpc_error(rsp)


class UnlockError(RpcError):

    def __init__(self, rsp):
        RpcError.__init__(self, rsp=rsp)
        self.rpc_error = jxml.rpc_error(rsp)
