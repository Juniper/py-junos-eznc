# stdlib
import hashlib
from os import path

# 3rd-party modules
from lxml.builder import E

# jnpr.eznc modules
from .ezutil import EzUtil
from .ncscp import SCP 

class SW(EzUtil):
  """
  Softawre Utility class, used to perform a software upgrade and associated functions.
  """

  @classmethod
  def sha256(cls,package):
    """
    computes the SHA-256 value on the package file.  This value should then be
    passed to the :install(): method.  This method would generally be used if 
    the same file was being loaded on a number of devices; thereby not re-calculating 
    the sha256 hexdigest each time the file was loaded onto a different box.
    """
    def hashfile(afile, hasher,blocksize=65536):
      buf = afile.read(blocksize)
      while len(buf) > 0:
          hasher.update(buf)
          buf = afile.read(blocksize)
      return hasher.hexdigest()      

    return hashfile(open(package,'rb'),hashlib.sha256())

  def put(self, package, remote_path='/var/tmp', progress=None):
    """
    scp put the package file from the local server to the remote device
    """
    def _progress(report): 
      if progress is not None: progress(self._dev, report)

    def _scp_progress(_path, _total, _xfrd):
      # init static variable
      if not hasattr(_scp_progress,'by10pct'): _scp_progress.by10pct = 0

      # calculate current percentage xferd
      pct = int(float(_xfrd)/float(_total) * 100)

      # if 10% more has been copied, then print a message
      if 0 == (pct % 10) and pct != _scp_progress.by10pct:
        _scp_progress.by10pct = pct
        _progress("%s: %s / %s (%s%%)" % (_path,_xfrd,_total,str(pct)))

    with SCP(self._dev, progress=_scp_progress) as scp:
      scp.put(package, remote_path)

  def pkgadd(self, remote_package, validate=False):    
    """ issue the 'request system software add' command on the package """
    # now perform the request install command.
    pkgadd_opts = {}
    pkgadd_opts[('no_validate','validate')[validate]] = True
    pkgadd_opts['package_name'] = remote_package
    rsp = self._dev.rpc.request_package_add(**pkgadd_opts)

    got = rsp.getparent()
    rc = int(got.findtext('package-result').strip())
    return True if rc == 0 else got.findtext('output').strip()

  ### -------------------------------------------------------------------------
  ### install - complete installation process, but not reboot
  ### -------------------------------------------------------------------------

  def install(self, package, remote_path='/var/tmp', validate=False, sha256=None, cleanfs=True, progress=None):
    """
    Installs a Junos package.  Effectively the same as
    '> request system software add ...'

    You will need to invoke the :reboot(): method explicity to reboo the device.

    :package: 
      is the tarball on the server filesystem.  
    
    :remote_path: 
      is the directory on the Junos device where the package file will be SCP'd to.  
    
    :validate:
      determines whether or not to perform a config validation against the new image

    :sha256:
      SHA-256 hexdigest of the package file.  If this is not provided, then this
      method will perform the calculation.  If you are planning on using the
      same image for multiple updates, you should consider using the :sha256():
      method to precalculate this value and then provide to this method.

    :cleanfs:
      determines whether or not to perform a 'storeage cleanup' before SCP'ing 
      the file to the device.

    :progress:
      if provided, this is a callback function with a function prototype given
      the Netconf instance and the report string, e.g.
        
        def myprogress(dev, report):
          print "host: %s, report: %s" % (dev.hostname, report)
    """
    def _progress(report): 
      if progress is not None: progress(self._dev, report)
    
    rpc = self._dev.rpc

    if sha256 is None: 
      _progress('computing local SHA-256 on: %s' % package)
      sha256 = SW.sha256(package)

    if cleanfs is True:
      _progress('cleaning filesystem ...')
      rpc.request_system_storage_cleanup()

    self.put( package, remote_path, progress)

    # validate checksum:
    remote_package = remote_path + '/' + path.basename(package)
    _progress('computing remote SHA-256 on: %s' % remote_package)
    rsp = rpc.get_sha256_checksum_information(path=remote_package)
    remote_sha256 = rsp.findtext('.//checksum').strip()

    if remote_sha256 != sha256:
      _progress("SHA-256 check failed.")
      return False
    _progress("SHA-256 check passed.")

    _progress("installing software ... this could take some time, please be patient ...")
    rsp = self.pkgadd( remote_package, validate=validate)
    return rsp

  def reboot(self, in_min=0):    
    """ perform a system reboot, with optional delay """
    rpc = E('request-reboot', E('in', str(in_min)))
    rsp = self._dev.rpc(rpc)
    return rsp.findtext('request-reboot-status').strip()
