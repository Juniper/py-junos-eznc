from lxml import etree
from jnpr.junos import jxml


class RpcError(Exception):
    """
    Parent class for all junos-pyez RPC Exceptions
    """
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
    """
    Generated in response to a commit-check or a commit action.
    """
    def __init__(self, cmd=None, rsp=None, errs=None):
        RpcError.__init__(self, cmd, rsp, errs)
        self.rpc_error = jxml.rpc_error(rsp)


class LockError(RpcError):
    """
    Generated in response to attempting to take an exclusive
    lock on the configuration database.
    """
    def __init__(self, rsp):
        RpcError.__init__(self, rsp=rsp)
        self.rpc_error = jxml.rpc_error(rsp)


class UnlockError(RpcError):
    """
    Generated in response to attempting to unlock the 
    configuration database.
    """
    def __init__(self, rsp):
        RpcError.__init__(self, rsp=rsp)
        self.rpc_error = jxml.rpc_error(rsp)

class PermissionError(RpcError):
    """
    Generated in response to invoking an RPC for which the
    auth user does not have user-class permissions.
    """
    pass

#### ================================================================
#### ================================================================
####                    Connection Exceptions
#### ================================================================
#### ================================================================

class ConnectError(object):
    """
    Parent class for all connection related exceptions
    """
    def __init__(self, dev):
        self.dev = dev
        # @@@ need to attach attributes for each access
        # @@@ to user-name, host, jump-host, etc.

class ConnectAuthError(ConnectError): 
    """
    Generated if the user-name, password is invalid
    """
    pass

class ConnectTimeoutError(ConnectError):
    """
    Generated if the NETCONF session fails to connect 
    after a sepcific timeout
    """
    pass

class ConnectUnreachableError(ConnectError):
    """
    Generated if the specified host is not reachable;
    could be due to routing, bad host-name, ip-addr, etc.
    """
    pass

class ConnectNetconfError(ConnectError):
    """
    Generated if the specified host denies the NETCONF; could
    be that the serivces is not enabled, or the host has
    too many connections already.
    """
    pass

class ConnectNotMasterError(ConnectError):
    """
    Generated if the connection is made to a non-master
    routing-engine.  This could be a backup RE on an MX
    device, or a virtual-chassis member (linecard), for example
    """
    pass