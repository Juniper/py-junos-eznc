from lxml import etree

class RpcError( Exception ):

  def __init__( self, cmd=None, rsp=None, errs=None ):
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
    if None != rsp:
      return etree.tostring(self.rsp, pretty_print=True)
    else:
      return

class CommitError( RpcError ):
  def __init__(self,cmd = None, rsp=None, errs = None):
    RpcError.__init__( self, cmd, rsp, errs )

class LockError( RpcError ):
  def __init__(self):
    RpcError.__init__(self)

class UnlockError( RpcError ):
  def __init__(self):
    RpcError.__init__(self)
