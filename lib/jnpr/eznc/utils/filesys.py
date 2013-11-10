import pdb

from lxml.builder import E

class FS(object):
  """
  Filesystem (FS) utilities:
    cat - show the contents of a file
    copy - local file copy (not scp)
    rename - local file rename
    delete - local file delete
    cwd - change working directory
    pwd - get working directory
    checksum - calculate file checksum (md5,sha256,sha1)
    stat - return file/dir information
    list - return file/dir listing
    storage_usage - return storage usage
    storage_cleanup - perform storage storage_cleanup
    storage_cleanup_check - returns a list of files to remove at cleanup

  """
  def __init__(self,nc):
    """ nc, Netconf """
    self._nc = nc

  ### -------------------------------------------------------------------------
  ### cat - show file contents
  ### -------------------------------------------------------------------------

  def cat(self,path):
    try:
      rsp = self._nc.rpc.file_show(filename=path)
    except:
      return None
    return rsp.text

  ### -------------------------------------------------------------------------
  ### cwd - change working directory
  ### -------------------------------------------------------------------------

  def cwd(self, path):
    """
    change working directory to path
    """
    self._nc.rpc.set_cli_working_directory(directory=path)

  ### -------------------------------------------------------------------------
  ### pwd - return current working directory
  ### -------------------------------------------------------------------------

  def pwd(self):
    """
    returns the current working directory
    """
    rsp = self._nc.rpc(E.command("show cli directory"))
    return rsp.findtext('./working-directory')

  ### -------------------------------------------------------------------------
  ### checksum - compute file checksum
  ### -------------------------------------------------------------------------

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

  @classmethod
  def _decode_file(cls, fileinfo):
    results = {}

    not_file = fileinfo.xpath('file-directory | file-symlink-target')
    if len(not_file):
      results['type'] = {'file-directory':'dir', 'file-symlink-target':'link'}[not_file[0].tag]
      if 'link' == results['type']:
        results['link'] = not_file[0].text.strip()
    else:    
      results['type'] = 'file'

    results['path'] = fileinfo.findtext('file-name').strip()
    results['owner'] = fileinfo.findtext('file-owner').strip()
    results['size'] = int(fileinfo.findtext('file-size'))
    fper = fileinfo.find('file-permissions')
    results['permissions'] = int(fper.text.strip())
    results['permissions_text'] = fper.get('format')
    fdate = fileinfo.find('file-date')
    results['ts_date'] = fdate.get('format')
    results['ts_epoc'] = fdate.text.strip()
    return results

  @classmethod
  def _decode_dir(cls, dirinfo, files=None):
    results = {}
    results['type'] = 'dir'
    results['path'] = dirinfo.get('name')
    if files is None: files = dirinfo.xpath('file-information')
    results['file_count'] = len(files)
    results['size'] = sum([int(f.findtext('file-size')) for f in files])
    return results

  ### -------------------------------------------------------------------------
  ### stat - file information
  ### -------------------------------------------------------------------------

  def stat(self,path):
    """
    Returns a dictionary of status information on the path, or None
    if the path does not exist.  

    @@@ MORE NEEDED @@@
    """
    rsp = self._nc.rpc.file_list(detail=True, path=path)

    # if there is an output tag, then it means that the path
    # was not found
    if rsp.find('output') is not None: return None

    # ok, so we've either got a directory or a file at 
    # this point, so decode accordingly

    xdir = rsp.find('directory')
    if xdir.get('name'): # then this is a directory path
      return FS._decode_dir(xdir)
    else:
      return FS._decode_file(xdir.find('file-information'))

  ### -------------------------------------------------------------------------
  ### list - file/dir listing
  ### -------------------------------------------------------------------------

  def list(self, path, followlink=True):
    """
    File listing, returns a dict of file information.  If the
    path is a symlink, then by default (:followlink):) will
    recursively call this method to obtain the symlink specific
    information.
    """
    rsp = self._nc.rpc.file_list(detail=True, path=path)

    # if there is an output tag, then it means that the path
    # was not found, and we return :None:

    if rsp.find('output') is not None: return None

    xdir = rsp.find('directory')

    # check to see if the directory element has a :name:
    # attribute, and if it does not, then this is a file, and
    # decode accordingly.  If the file is a symlink, then we
    # want to follow the symlink to get what we want.

    if not xdir.get('name'): 
      results = FS._decode_file(xdir.find('file-information'))
      link_path = results.get('link')
      if not link_path: # then we are done
        return results
      else:
        return results if followlink is False else self.list(path=link_path)

    # if we are here, then it's a directory, include information on all files
    files = xdir.xpath('file-information')
    results = FS._decode_dir(xdir, files)

    results['files'] = {
      f.findtext('file-name').strip():FS._decode_file(f)
      for f in files
    }

    return results

  ### -------------------------------------------------------------------------
  ### storage_usage - filesystem storage usage
  ### -------------------------------------------------------------------------

  def storage_usage(self):
    rsp = self._nc.rpc.get_system_storage()

    _name = lambda fs: fs.findtext('filesystem-name').strip()

    def _decode(fs):
      r = {}
      r['mount'] = fs.find('mounted-on').text.strip()
      tb = fs.find('total-blocks')
      r['total'] = tb.get('format')        
      r['total_blocks'] = int(tb.text)
      ub = fs.find('used-blocks')
      r['used'] = ub.get('format')        
      r['used_blocks'] = int(ub.text)
      r['used_pct'] = fs.find('used-percent').text.strip()
      ab = fs.find('available-blocks')
      r['avail'] = ab.get('format')        
      r['avail_block'] = int(ab.text)
      return r

    return { _name(fs): _decode(fs)
      for fs in rsp.xpath('filesystem')
    }

  ### -------------------------------------------------------------------------
  ### storage_cleanup
  ### -------------------------------------------------------------------------

  def storage_cleanup(self):
    pass

  ### -------------------------------------------------------------------------
  ### storage_cleanup_check
  ### -------------------------------------------------------------------------

  def storage_cleanup_check(self):
    rsp = self._nc.rpc.request_system_storage_cleanup(dry_run=True)
    files = rsp.xpath('file-list/file')

    _name = lambda f: f.findtext('file-name').strip()
    def _decode(f):
      return {
        'size' : int(f.findtext('size')),
        'ts_date' : f.findtext('date').strip()
      }
    return { _name(f): _decode(f) for f in files }


    


