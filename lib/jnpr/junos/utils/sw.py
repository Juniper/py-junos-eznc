# stdlib
import hashlib
from os import path

# 3rd-party modules
from lxml.builder import E

# local modules
from .util import Util
from .scp import SCP 

class SW(Util):
  """
  Softawre Utility class, used to perform a software upgrade and associated functions.

  Primary methods:
    sha256 - (class method) to compute SHA-256 hexdigest
    install - perform the entire software installation process
    reboot - reboots the system for the new image to take effect    
    poweroff - shutdown the system

  Helpers called from install, but you can use these individually if needed:
    put - SCP put package file onto Junos device
    pkgadd - performs the 'request' operation to install the package
    validate - performs the 'request' to validate the package

  Other utils:
    rollback - same as 'request softare rollback'
    inventory - (property) provides file info for current and rollback 
                images on the device
  """

  @classmethod
  def sha256(cls,package):
    """
    computes the SHA-256 value on the package file.  This value should then be
    passed to the :install(): method.  This method would generally be used if 
    the same file was being loaded on a number of devices; thereby not re-calculating 
    the sha256 hexdigest each time the file was loaded onto a different box.

    :package:
      complete path to the package (*.tgz) file on the local server      
    """
    def hashfile(afile, hasher,blocksize=65536):
      buf = afile.read(blocksize)
      while len(buf) > 0:
          hasher.update(buf)
          buf = afile.read(blocksize)
      return hasher.hexdigest()      

    return hashfile(open(package,'rb'),hashlib.sha256())

  @classmethod
  def progress(cls,dev,report):
    """ simple progress report function """
    print dev.hostname + ": " + report

  ### -------------------------------------------------------------------------
  ### put - SCP put the image onto the device
  ### -------------------------------------------------------------------------

  def put(self, package, remote_path='/var/tmp', progress=None):
    """
    SCP 'put' the package file from the local server to the remote device.

    :remote_path:
      the directory on the device where the package will be copied to

    :progress:
      callback function to indicate progress.  see :install(): for details
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

  ### -------------------------------------------------------------------------
  ### pkgadd - used to perform the 'request system software add ...'
  ### -------------------------------------------------------------------------

  def pkgadd(self, remote_package ):    
    """ issue the 'request system software add' command on the package """

    rsp = self.rpc.request_package_add( no_validate=True, 
      package_name=remote_package )

    got = rsp.getparent()
    rc = int(got.findtext('package-result').strip())
    return True if rc == 0 else got.findtext('output').strip()

  ### -------------------------------------------------------------------------
  ### validate - perform 'request' operation to validate the package
  ### -------------------------------------------------------------------------

  def validate(self, remote_package):
    """ issues the 'request' operation to validate the package against the config """
    rsp = self.rpc.request_package_validate(package_name=remote_package).getparent()
    errcode = int(rsp.findtext('package-result'))
    return True if 0 == errcode else rsp.findtext('output').strip()

  ### -------------------------------------------------------------------------
  ### install - complete installation process, but not reboot
  ### -------------------------------------------------------------------------

  def install(self, package, remote_path='/var/tmp', validate=False, sha256=None, cleanfs=True, progress=None):
    """
    Performs the complete installation of the :package: that includes the following steps:
      (1) computes the SHA-256 checksum if not provided in :sha256:
      (2) performs a storage cleanup if :cleanfs: is True
      (3) SCP copies the package to the :remote_path: directory
      (4) validates the package if :validate: is True
      (5) installs the package

    You can get a progress report on this process by providing a :progress: callback;
    see description below.

    You will need to invoke the :reboot(): method explicity to reboot the device.

    :package: 
      is the install package tarball on the local filesystem.
    
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
      the Device instance and the report string, e.g.
        
        def myprogress(dev, report):
          print "host: %s, report: %s" % (dev.hostname, report)
    """
    def _progress(report): 
      if progress is not None: progress(self._dev, report)
    
    rpc = self.rpc

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

    if validate is True:
      _progress("validating software against current config, please be patient ...")
      v_ok = self.validate(remote_package)
      if v_ok is not True:
        return v_ok # will be the string of output

    _progress("installing software ... this could take some time, please be patient ...")
    rsp = self.pkgadd( remote_package )
    return rsp

  ### -------------------------------------------------------------------------
  ### rebbot - system reboot
  ###
  ### @@@ - need to broader support to multi-RE devices
  ### -------------------------------------------------------------------------

  def reboot(self, in_min=0):    
    """ perform a system reboot, with optional delay (in minutes) """
    rsp = self.rpc(E('request-reboot', E('in', str(in_min))))
    return rsp.findtext('request-reboot-status').strip()

  ### -------------------------------------------------------------------------
  ### poweroff - system shutdown
  ###
  ### @@@ - need to broader support to multi-RE devices
  ### -------------------------------------------------------------------------

  def poweroff(self, in_min=0):    
    """ perform a system shutdown, with optional delay (in minutes) """
    rsp = self.rpc(E('request-power-off', E('in', str(in_min))))
    return rsp.findtext('request-reboot-status').strip()

  ### -------------------------------------------------------------------------
  ### rollback - clears the install request
  ### -------------------------------------------------------------------------

  def rollback(self):
    """ 
    issues the 'request' command to do the rollback and returns the string
    output of the results
    """
    rsp = self.rpc.request_package_rollback()
    return rsp.text.strip()

  ### -------------------------------------------------------------------------
  ### inventory - file info on current and rollback packages
  ### -------------------------------------------------------------------------

  @property
  def inventory(self):
    """
    returns a dictionary of file listing information for current and rollback
    Junos install packages.  This information comes from the /packages directory.
    """
    from .fs import FS 
    fs = FS(self.dev)
    pkgs = fs.ls('/packages') 
    return dict(current=pkgs['files'].get('junos'), rollback=pkgs['files'].get('junos.old'))
