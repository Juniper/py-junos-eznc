
from lxml.builder import E

class FS(object):
  """
  Filesystem (FS) utilities
  """
  def __init__(self,nc):
    """
    nc, Netconf
    """
    self._nc = nc

  def cwd(self, path):
    """
    change working directory to path
    """
    self._nc.rpc.set_cli_working_directory(directory=path)

  def pwd(self):
    """
    returns the current working directory
    """
    rsp = self._nc.rpc(E.command("show cli directory"))
    return rsp.findtext('./working-directory')


  def checksum(self, path, calc='md5' ):
    """
    performs the checksum command on the given file path using the 
    required calculation method ['md5', 'sha256', 'sha1'] and returns
    the string value.  if the :path: is not found on the device, then
    None is returned.
    """
    cmd_map = {
      'md5' : self._nc.rpc.get_checksum_information,
      'sha256' : self._nc.rpc.get_sha256_checksum_information,
      'sha1' : self._nc.rpc.get_sha1_checksum_information
    }
    rpc = cmd_map.get(calc)
    if rpc is None: raise ValueError("Unknown calculation method: '%s'" % calc)
    try:
      rsp = rpc(path=path)
      return rsp.findtext('.//checksum').strip()
    except:
      # the only exception is that the path is not found
      return None
    


