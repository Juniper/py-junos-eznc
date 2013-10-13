import pdb

import re
from lxml import etree

class _RpcMetaExec(object):
  def __init__(self, junos):
    """
      ~PRIVATE CLASS~
      creates an RPC meta-executor object bound to the provide
      :junos: object
    """
    self._junos = junos

  def __getattr__( self, rpc_cmd_name ):
    """
      metaprograms a function to execute the :rpc_cmd_name:

      the caller will be passing (*vargs, **kvargs) on
      execution of the meta function; these are the specific
      rpc command arguments(**kvargs) and options bound
      as XML attributes (*vargs)
    """
    
    rpc_cmd = re.sub('_','-', rpc_cmd_name)

    def _exec_rpc(*vargs, **kvargs):
      # create the rpc as XML command
      rpc = etree.Element( rpc_cmd )
      if kvargs:
        for arg_name, arg_value in kvargs.items():
          arg_name = re.sub('_','-',arg_name)               
          arg = etree.SubElement( rpc, arg_name )
          if arg_value != True: arg.text = arg_value

      # now invoke the command against the
      # associated :junos: device and return
      # the results per :junos:execute()

      return self._junos.execute(rpc)

    # metabind help() and the function name to the :rpc_cmd_name:
    # provided by the caller ... that's about all we can do, yo!

    _exec_rpc.__doc__ = rpc_cmd
    _exec_rpc.__name__ = rpc_cmd_name

    # return the metafunction that the caller will in-turn invoke
    return _exec_rpc

  def __call__( self, rpc_cmd ):
    """
      callable will execute the provided :rpc_cmd: against the
      attached :junos: object and retur the RPC response per 
      :junos:execute()
    """
    return True
