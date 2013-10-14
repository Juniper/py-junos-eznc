from lxml import etree

class RpcError( StandardError ):

  def __init__( self, cmd, rsp, errs ):
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
    return etree.tostring(self.rsp, pretty_print=True)
