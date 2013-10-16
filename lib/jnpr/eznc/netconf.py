
import pdb

from lxml import etree
from ncclient import manager as netconf_ssh

from .rpcmeta import _RpcMetaExec
from .exception import RpcError
from .ez import Manager as EzMgr

class Netconf(object):

  ##### -------------------------------------------------------------------------
  ##### PROPERTIES
  ##### -------------------------------------------------------------------------

  ### ---------------------------------------------------------------------------
  ### property: hostname
  ### ---------------------------------------------------------------------------

  @property
  def hostname(self):
    """
      The hostname/ip-addr of the Junos device
    """
    return self._hostname

  ### ---------------------------------------------------------------------------
  ### property: user
  ### ---------------------------------------------------------------------------
  
  @property
  def user(self):
    """
      The login user accessing the Junos device
    """
    return self._user

  ### ---------------------------------------------------------------------------
  ### property: password
  ### ---------------------------------------------------------------------------

  @property
  def password(self):
    """
      The login password to access the Junos deviec
    """
    return None  # read-only      

  @password.setter
  def password(self, value):
    self._password = value
  
  ### ---------------------------------------------------------------------------
  ### property: logfile
  ### ---------------------------------------------------------------------------

  @property
  def logfile(self):
    """
      simply returns the log file object
    """
    return self._logfile

  @logfile.setter
  def logfile(self, value):
    """
      assigns an opened file object to the device for logging
      If there is an open logfile, and 'value' is None/False
      then close the existing file
    """
    # got an existing file that we need to close
    if (not value) and (None != self._logfile):
      rc = self._logfile.close()
      self._logfile = False
      return rc

    if not isinstance(value, file):
      raise ValueError("value must be a file object")  

    self._logfile = value
    return self._logfile

  ##### -----------------------------------------------------------------------
  ##### CONSTRUCTOR
  ##### -----------------------------------------------------------------------

  def __init__(self, *vargs, **kvargs):
    """
      Required args:
        user: login user name
        host: host-name or ip-addr

      Optional args:
        password: login user password; if not provided, assumes ssh-keys
    """

    # private attributes

    self._hostname = kvargs['host']
    self._auth_user = kvargs['user']
    self._auth_password = kvargs['password']
    self._conn = None

    # public attributes

    self.connected = False
    self.rpc = _RpcMetaExec( self )
    self.ez = EzMgr( self )

  ##### -----------------------------------------------------------------------
  ##### Basic device methods
  ##### -----------------------------------------------------------------------

  def open( self, *vargs, **kvargs ):
    """
      opens a connection to the device using existing login/auth 
      information.  No additional options are supported; at this time
    """
    # open connection using ncclient transport
    self._conn =  netconf_ssh.connect( host=self.hostname,
      username=self._auth_user, password=self._auth_password,
      hostkey_verify=False )

    self.connected = True

  def close( self ):
    """
      closes the connection to the device
    """
    self._conn.close_session()
    self.connected = False

  def execute( self, rpc_cmd, **kvargs ):
    """
      executes the :rpc_cmd: and returns the result.  the result is an
      lxml Element following <rpc-reply> unless the caller specifies
      a :to_py: param

      :rpc_cmd: can either be an Element or xml-as-string.  In either case
      the command starts with the specific command element, i.e., not the
      <rpc> element itself

      KNOWN options for kvargs:
        :to_py: is a caller provided function that takes the response and
                will convert the results to native python types.  all kvargs
                will be passed to this function as well in the form:
                :to_py:( self, rpc_rsp_e, **kvargs )
    """

    if isinstance(rpc_cmd, str):
      rpc_cmd_e = etree.XML( rpc_cmd )
    elif isinstance(rpc_cmd, etree._Element):
      rpc_cmd_e = rpc_cmd
    else:
      raise ValueError("Dont know what to do with rpc of type %s" % rpc_cmd.__class__.__name__)

    # invoking a bad RPC will cause a connection object exception
    # will will be raised directly to the caller ... for now ...
    # @@@ need to trap this and re-raise accordingly.

    rpc_rsp_e = self._conn.rpc( rpc_cmd_e )._NCElement__doc

    # for RPCs that have embedded rpc-errors, need to check for those now

    rpc_errs = rpc_rsp_e.xpath('.//rpc-error')
    if len(rpc_errs):
      raise RpcError( rpc_cmd_e, rpc_rsp_e, rpc_errs )

    # skip the <rpc-reply> element and pass the caller the first child element
    # generally speaking this is what they really want.  if they want to uplevel 
    # they can always call the getparent() method on it.

    try:
      ret_rpc_rsp = rpc_rsp_e[0]    
    except IndexError:
      # no children, so assume it means we are OK
      return True

    # if the caller provided a "to Python" conversion function, then invoke
    # that now and return the results of that function.  otherwise just return
    # the RPC results as XML

    if kvargs.get('to_py'):
      return kvargs['to_py']( self, ret_rpc_rsp, **kvargs )
    else:
      return ret_rpc_rsp

  ##### -------------------------------------------------------------
  ##### Constructor buddies ...
  ##### -------------------------------------------------------------

  def Template( self, filename ):
    return True

