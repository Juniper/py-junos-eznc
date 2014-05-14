# stdlib
import os
import types
from inspect import isclass
import platform

# stdlib, in support of the the 'probe' method
import socket
import datetime
import time
import sys

# 3rd-party packages
from lxml import etree
from ncclient import manager as netconf_ssh
import ncclient.transport.errors as NcErrors
import paramiko
import jinja2

# local modules
from jnpr.junos.rpcmeta import _RpcMetaExec
from jnpr.junos import exception as EzErrors
from jnpr.junos.cfg import Resource
from jnpr.junos.facts import *
from jnpr.junos import jxml as JXML

_MODULEPATH = os.path.dirname(__file__)


class _MyTemplateLoader(jinja2.BaseLoader):

    """
    Create a jinja2 template loader class that can be used to
    load templates from all over the filesystem, but defaults
    to the CWD and the 'templates' directory of the module
    """

    def __init__(self):
        self.paths = ['.', os.path.join(_MODULEPATH, 'templates')]

    def get_source(self, environment, template):

        def _in_path(dir):
            return os.path.exists(os.path.join(dir, template))

        path = filter(_in_path, self.paths)
        if not path:
            raise jinja2.TemplateNotFound(template)

        path = os.path.join(path[0], template)
        mtime = os.path.getmtime(path)
        with file(path) as f:
            source = f.read().decode('utf-8')
        return source, path, lambda: mtime == os.path.getmtime(path)

_Jinja2ldr = jinja2.Environment(loader=_MyTemplateLoader())


class Device(object):
    ON_JUNOS = platform.system().upper() == 'JUNOS'    
    auto_probe = 0          # default is no auto-probe

    # -------------------------------------------------------------------------
    # PROPERTIES
    # -------------------------------------------------------------------------
    
    # ------------------------------------------------------------------------
    # property: hostname
    # ------------------------------------------------------------------------

    @property
    def hostname(self):
        """
        The hostname/ip-addr of the Junos device
        """
        return self._hostname if (
            self._hostname != 'localhost') else self.facts.get('hostname')

    # ------------------------------------------------------------------------
    # property: user
    # ------------------------------------------------------------------------

    @property
    def user(self):
        """
        The login user accessing the Junos device
        """
        return self._auth_user

    # ------------------------------------------------------------------------
    # property: password
    # ------------------------------------------------------------------------

    @property
    def password(self):
        """
          The login password to access the Junos deviec
        """
        return None  # read-only

    @password.setter
    def password(self, value):
        self._password = value

    # ------------------------------------------------------------------------
    # property: logfile
    # ------------------------------------------------------------------------

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

    # ------------------------------------------------------------------------
    # property: timeout
    # ------------------------------------------------------------------------

    @property
    def timeout(self):
        """ the netconf timeout value """
        return self._conn.timeout

    @timeout.setter
    def timeout(self, value):
        """ set the netconf timeout value """
        self._conn.timeout = value

    # ------------------------------------------------------------------------
    # property: facts
    # ------------------------------------------------------------------------

    @property
    def facts(self):
        return self._facts

    @facts.setter
    def facts(self, value):
        raise RuntimeError("facts is read-only!")

    # ------------------------------------------------------------------------
    # property: manages
    # ------------------------------------------------------------------------

    @property
    def manages(self):
        """
        returns a list of Resource Managers/Utilities attached to this
        isinstance using the :bind(): method
        """
        return self._manages

    # -----------------------------------------------------------------------
    # OVERLOADS
    # -----------------------------------------------------------------------

    def __repr__(self):
        return "Device(%s)" % self.hostname

    # -----------------------------------------------------------------------
    # CONSTRUCTOR
    # -----------------------------------------------------------------------

    def _sshconf_lkup(self):
        home = os.getenv('HOME')
        if not home:
            return
        sshconf_path = os.path.join(os.getenv('HOME'), '.ssh/config')
        if not os.path.exists(sshconf_path):
            return

        sshconf = paramiko.SSHConfig()
        sshconf.parse(open(sshconf_path, 'r'))
        found = sshconf.lookup(self._hostname)
        self._hostname = found.get('hostname', self._hostname)
        self._port = found.get('port', self._port)
        self._auth_user = found.get('user')

    def __init__(self, *vargs, **kvargs):
        """
        vargs[0] -- ALTERNATIVE for kvargs['host']

        kvargs['host'] -- REQUIRED for off-box
          device hostname or ipaddress

        kvargs['user'] -- OPTIONAL
          login user-name, uses $USER if not provided

        kvargs['password'] -- OPTIONAL
        kvargs['passwd'] -- OPTIONAL
          login password.  if not provided, assumed ssh-keys are enforced

        kvargs['port'] -- OPTIONAL
          device login port (defaults to 830)

        kvargs['gather_facts'] -- optional
          if :False: then the facts are not gathered on call to :open():

        kvargs['auto_probe'] -- OPTIONAL
            if non-zero then this enables auto_probe at time of :open():
            and defines the amount of time/seconds for the probe timeout
        """

        # ----------------------------------------
        # setup instance connection/open variables
        # ----------------------------------------

        hostname = vargs[0] if len(vargs) else kvargs.get('host')

        self._port = kvargs.get('port', 830)
        self._gather_facts = kvargs.get('gather_facts', True)
        self._auto_probe = kvargs.get('auto_probe', self.__class__.auto_probe)

        if self.__class__.ON_JUNOS is True and hostname is None:
            # ---------------------------------
            # running on a Junos device locally
            # ---------------------------------            
            self._auth_user = None
            self._auth_password = None
            self._hostname = 'localhost'
        else:
            # --------------------------            
            # making a remote connection
            # --------------------------
            if hostname is None:
                raise ValueError("You must provide the 'host' value")
            self._hostname = hostname
            # user will default to $USER
            self._auth_user = os.getenv('USER')
            # user can get updated by ssh_config
            self._sshconf_lkup()
            # but if user is explit from call, then use it.
            self._auth_user = kvargs.get('user') or self._auth_user
            self._auth_password = kvargs.get('password') or kvargs.get('passwd')
        
        # -----------------------------
        # initialize instance variables
        # ------------------------------

        self._conn = None
        self._j2ldr = _Jinja2ldr
        self._manages = []
        self._facts = {}

        # public attributes

        self.connected = False
        self.rpc = _RpcMetaExec(self)

    # -----------------------------------------------------------------------
    # Basic device methods
    # -----------------------------------------------------------------------

    def open(self, *vargs, **kvargs):
        """
        opens a connection to the device using existing login/auth
        information.

        kvargs['gather_facts']:
            If set to True/False will override the device instance value
            for only this open process

        kvargs['auto_probe']:
            if non-zero then this enables auto_probe and defines the amount 
            of time/seconds for the probe timeout
        """

        auto_probe = kvargs.get('auto_probe', self._auto_probe)
        if auto_probe is not 0:
            if not self.probe(auto_probe):
                raise EzErrors.ProbeError(self)

        try:
            ts_start = datetime.datetime.now()

            # open connection using ncclient transport
            self._conn = netconf_ssh.connect(
                host=self._hostname,
                port=self._port,
                username=self._auth_user,
                password=self._auth_password,
                hostkey_verify=False,
                device_params={'name': 'junos'})

        except NcErrors.AuthenticationError as err:
            # bad authentication credentials
            raise EzErrors.ConnectAuthError(self)

        except NcErrors.SSHError as err:
            # this is a bit of a hack for now, since we want to 
            # know if the connection was refused or we simply could
            # not open a connection due to reachability.  so using
            # a timestamp to differentiate the two conditions for now
            # if the diff is < 3 sec, then assume the host is 
            # reachable, but NETCONF connection is refushed. 

            ts_err = datetime.datetime.now()
            diff_ts = ts_err - ts_start
            if diff_ts.seconds < 3:
                raise EzErrors.ConnectRefusedError(self)

            # at this point, we assume that the connection
            # has timeed out due to ip-reachability issues

            if err.message.find('not open') > 0:
                raise EzErrors.ConnectTimeoutError(self)
            else:
                # otherwise raise a generic connection
                # error for now.  tag the new exception
                # with the original for debug
                cnx = EzErrors.ConnectError(self)
                cnx._orig = err
                raise cnx

        except socket.gaierror:
            # invalid DNS name, so unreachable
            raise EzErrors.ConnectUnknownHostError(self)

        except Exception as err:
            # anything else, we will re-raise as a
            # generic ConnectError
            cnx_err = EzErrors.ConnectError(self)
            cnx_err._orig = err 
            raise cnx_err

        self.connected = True

        gather_facts = kvargs.get('gather_facts', self._gather_facts)
        if gather_facts is True:
            self.facts_refresh()

        return self

    def close(self):
        """
        closes the connection to the device
        """
        self._conn.close_session()
        self.connected = False

    def execute(self, rpc_cmd, **kvargs):
        """
        Executes an XML RPC and returns results as either XML or native python

        rpc_cmd
          can either be an XML Element or xml-as-string.  In either case
          the command starts with the specific command element, i.e., not the
          <rpc> element itself

        kvargs['to_py']
          is a caller provided function that takes the response and
          will convert the results to native python types.  all kvargs
          will be passed to this function as well in the form:
          :to_py:( self, rpc_rsp, \**kvargs )
        """

        if isinstance(rpc_cmd, str):
            rpc_cmd_e = etree.XML(rpc_cmd)
        elif isinstance(rpc_cmd, etree._Element):
            rpc_cmd_e = rpc_cmd
        else:
            raise ValueError(
                "Dont know what to do with rpc of type %s" %
                rpc_cmd.__class__.__name__)

        # invoking a bad RPC will cause a connection object exception
        # will will be raised directly to the caller ... for now ...
        # @@@ need to trap this and re-raise accordingly.

        try:
            rpc_rsp_e = self._conn.rpc(rpc_cmd_e)._NCElement__doc
        except Exception as err:
            # err is an NCError from ncclient
            rsp = JXML.remove_namespaces(err.xml)
            # see if this is a permission error
            e = EzErrors.PermissionError if rsp.findtext('error-message') == 'permission denied' else EzErrors.RpcError
            raise e(cmd=rpc_cmd_e, rsp=rsp)

        # for RPCs that have embedded rpc-errors, need to check for those now

        rpc_errs = rpc_rsp_e.xpath('.//rpc-error')
        if len(rpc_errs):
            raise EzErrors.RpcError(rpc_cmd_e, rpc_rsp_e, rpc_errs)

        # skip the <rpc-reply> element and pass the caller first child element
        # generally speaking this is what they really want. If they want to
        # uplevel they can always call the getparent() method on it.

        try:
            ret_rpc_rsp = rpc_rsp_e[0]
        except IndexError:
            # no children, so assume it means we are OK
            return True

        # if the caller provided a "to Python" conversion function, then invoke
        # that now and return the results of that function.  otherwise just
        # return the RPC results as XML

        if kvargs.get('to_py'):
            return kvargs['to_py'](self, ret_rpc_rsp, **kvargs)
        else:
            return ret_rpc_rsp

    # ------------------------------------------------------------------------
    # cli - for cheating commands :-)
    # ------------------------------------------------------------------------

    def cli(self, command, format='text'):
        """
        Executes the CLI command and returns the CLI text output by default.

        command
          The CLI command to execute, e.g. "show version"

        format
          The return format, by default is text.  You can optionally select
          'xml' to return the XML structure.

        Notes:
          You can also use this method to obtain the XML RPC command for a
          given CLI command by using the pipe filter "| display xml rpc". When
          you do this, the return value is the XML RPC command. For example if
          you provide as the command "show version | display xml rpc", you will
          get back the XML Element <get-software-information>
        """
        try:
            rsp = self.rpc.cli(command, format)
            if rsp.tag == 'output':
                return rsp.text
            if rsp.tag == 'configuration-information':
                return rsp.findtext('configuration-output')
            if rsp.tag == 'rpc':
                return rsp[0]
            return rsp
        except:
            return "invalid command: " + command

    # ------------------------------------------------------------------------
    # Template: retrieves a Jinja2 template
    # ------------------------------------------------------------------------

    def Template(self, filename, parent=None, gvars=None):

        # templates are XML files, and the assumption here is that they will
        # have .xml extensions.  if the caller doesn't include any extension
        # be kind and add '.xml' for them

        if os.path.splitext(filename)[1] == '':
            filename = filename + '.xml'

        return self._j2ldr.get_template(filename, parent, gvars)

    # ------------------------------------------------------------------------
    # dealing with bind aspects
    # ------------------------------------------------------------------------

    def bind(self, *vargs, **kvargs):
        """
        Used to attach things to this Device instance

        vargs
          a list of functions that will get bound as instance methods to
          this Device instance

        kvargs
          name/class pairs that will create resource-managers bound as
          instance attributes to this Device instance
        """
        if len(vargs):
            for fn in vargs:
                # check for name clashes before binding
                if hasattr(self, fn.__name__):
                    raise ValueError(
                        "request attribute name %s already exists" %
                        fn.__name__)
            for fn in vargs:
                # bind as instance method, majik.
                self.__dict__[
                    fn.__name__] = types.MethodType(
                    fn,
                    self,
                    self.__class__)
            return

        # first verify that the names do not conflict with
        # existing object attribute names

        for name in kvargs.keys():
            # check for name-clashes before binding
            if hasattr(self, name):
                raise ValueError(
                    "requested attribute name %s already exists" %
                    name)

        # now instantiate items and bind to this :Device:
        for name, thing in kvargs.items():
            new_inst = thing(self)
            self.__dict__[name] = new_inst
            self._manages.append(name)

    # ------------------------------------------------------------------------
    # facts
    # ------------------------------------------------------------------------

    def facts_refresh(self):
        """
        reload the facts from the Junos device into :facts: property
        """
        for gather in FACT_LIST:
            gather(self, self._facts)

    # ------------------------------------------------------------------------
    # probe
    # ------------------------------------------------------------------------

    def probe(self, timeout=5, intvtimeout=1):
        """
        Probe the device to determine if the Device can accept a remote
        connection.
        This method is meant to be called *prior* to :open():
        This method will not work with ssh-jumphost environments.

        :timeout:
          the probe will report True/False if the device report connectivity
          within this timeout (seconds)

        :intvtimeout:
          timeout interval on the socket connection. Generally you should not
          change this value, but you can if you want to twiddle the frequency
          of the socket attempts on the connection
        """
        start = datetime.datetime.now()
        end = start + datetime.timedelta(seconds=timeout)
        probe_ok = True

        while datetime.datetime.now() < end:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(intvtimeout)
            try:
                s.connect((self.hostname, self._port))
                s.shutdown(socket.SHUT_RDWR)
                s.close()
                break
            except:
                time.sleep(1)
                pass
        else:
            elapsed = datetime.datetime.now() - start
            probe_ok = False

        return probe_ok
