import pdb
import re
from lxml import etree
from lxml.builder import E

class _RpcMetaExec(object):

  ##### -----------------------------------------------------------------------
  ##### CONSTRUCTOR
  ##### -----------------------------------------------------------------------

  def __init__(self, junos):
    """
      ~PRIVATE CLASS~
      creates an RPC meta-executor object bound to the provided
      ez-netconf :junos: object
    """
    self._junos = junos

  ##### -----------------------------------------------------------------------
  ##### get_config
  ##### -----------------------------------------------------------------------

  def get_config( self, filter_xml=None, options=None ):
    rpc = E('get-configuration')

    if filter_xml != None:
      etree.SubElement(rpc, 'configuration').append( filter_xml )

    return self._junos.execute( rpc )

  def load_config( self, config_xml, options=None ):
    rpc = E('load-configuration')
    etree.SubElement(rpc, 'configuration').append( config_xml )
    if len(options): 
      for k,v in options.items(): rpc.attrib[k] = v

    pdb.set_trace()
    
    return self._junos.execute( rpc )

  ##### -----------------------------------------------------------------------
  ##### method missing
  ##### -----------------------------------------------------------------------

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

      # kvargs are the command parameter/values
      if kvargs:
        for arg_name, arg_value in kvargs.items():
          arg_name = re.sub('_','-',arg_name)               
          arg = etree.SubElement( rpc, arg_name )
          if arg_value != True: arg.text = arg_value

      # vargs[0] is a dict, command options like format='text'
      if vargs:
        for k,v in vargs[0].items():
          rpc.attrib[k] = v

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

  ##### -----------------------------------------------------------------------
  ##### callable
  ##### -----------------------------------------------------------------------

  def __call__( self, rpc_cmd, **kvargs ):
    """
      callable will execute the provided :rpc_cmd: against the
      attached :junos: object and return the RPC response per 
      :junos:execute()

      kvargs is simply passed 'as-is' to :junos:execute()
    """
    return self._junos.execute( rpc_cmd, **kvargs )
