# stdlib
import os
import types
import platform
import warnings
import traceback

# stdlib, in support of the the 'probe' method
import socket
import datetime
import time
import sys
import json
import re

# 3rd-party packages
from lxml import etree
from ncclient import manager as netconf_ssh
import ncclient.transport.errors as NcErrors
import ncclient.operations.errors as NcOpErrors
from ncclient.operations import RPCError
import paramiko
import jinja2

# local modules
from jnpr.junos.rpcmeta import _RpcMetaExec
from jnpr.junos import exception as EzErrors
from jnpr.junos.facts import *
from jnpr.junos import jxml as JXML
from jnpr.junos.decorators import timeoutDecorator, normalizeDecorator


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

        path = list(filter(_in_path, self.paths))
        if not path:
            raise jinja2.TemplateNotFound(template)

        path = os.path.join(path[0], template)
        mtime = os.path.getmtime(path)
        with open(path) as f:
            # You are trying to decode an object that is already decoded.
            # You have a str, there is no need to decode from UTF-8 anymore.
            # open already decodes to Unicode in Python 3 if you open in text mode.
            # If you want to open it as bytes, so that you can then decode,
            # you need to open with mode 'rb'.
            source = f.read()
        return source, path, lambda: mtime == os.path.getmtime(path)

_Jinja2ldr = jinja2.Environment(loader=_MyTemplateLoader())


class _Connection(object):

    # ------------------------------------------------------------------------
    # property: hostname
    # ------------------------------------------------------------------------

    @property
    def hostname(self):
        """
        :returns: the host-name of the Junos device.
        """
        return self._hostname if (
            self._hostname != 'localhost') else self.facts.get('hostname')

    # ------------------------------------------------------------------------
    # property: user
    # ------------------------------------------------------------------------

    @property
    def user(self):
        """
        :returns: the login user (str) accessing the Junos device
        """
        return self._auth_user

    # ------------------------------------------------------------------------
    # property: password
    # ------------------------------------------------------------------------

    @property
    def password(self):
        """
        :returns: ``None`` - do not provide the password
        """
        return None  # read-only

    @password.setter
    def password(self, value):
        """
        Change the authentication password value.  This is handy in case
        the calling program needs to attempt different passwords.
        """
        self._auth_password = value

    # ------------------------------------------------------------------------
    # property: logfile
    # ------------------------------------------------------------------------

    @property
    def logfile(self):
        """
        :returns: exsiting logfile ``file`` object.
        """
        return self._logfile

    @logfile.setter
    def logfile(self, value):
        """
        Assigns an opened file object to the device for logging
        If there is an open logfile, and 'value' is ``None`` or ``False``
        then close the existing file.

        :param file value: An open ``file`` object.

        :returns: the new logfile ``file`` object

        :raises ValueError:
            When **value** is not a ``file`` object
        """
        # got an existing file that we need to close
        if (not value) and (None != self._logfile):
            rc = self._logfile.close()
            self._logfile = False
            return rc

        if sys.version < '3':
            if not isinstance(value, file):
                raise ValueError("value must be a file object")
        else:
            import io
            if not isinstance(value, io.TextIOWrapper):
                raise ValueError("value must be a file object")

        self._logfile = value
        return self._logfile

    # ------------------------------------------------------------------------
    # property: timeout
    # ------------------------------------------------------------------------

    @property
    def timeout(self):
        """
        :returns: the current RPC timeout value (int) in seconds.
        """
        return self._conn.timeout

    @timeout.setter
    def timeout(self, value):
        """
        Used to change the RPC timeout value (default=30 sec).

        :param int value:
            New timeout value in seconds
        """
        self._conn.timeout = value

    # ------------------------------------------------------------------------
    # property: facts
    # ------------------------------------------------------------------------

    @property
    def facts(self):
        """
        :returns: Device fact dictionary
        """
        return self._facts

    @facts.setter
    def facts(self, value):
        """ read-only property """
        raise RuntimeError("facts is read-only!")

    # ------------------------------------------------------------------------
    # property: port
    # ------------------------------------------------------------------------

    @property
    def port(self):
        """
        :returns: the port (str) to connect to the Junos device
        """
        return self._port

    def _sshconf_lkup(self):
        if self._ssh_config:
            sshconf_path = os.path.expanduser(self._ssh_config)
        else:
            home = os.getenv('HOME')
            if not home:
                return None
            sshconf_path = os.path.join(os.getenv('HOME'), '.ssh/config')
        if not os.path.exists(sshconf_path):
            return None
        else:
            sshconf = paramiko.SSHConfig()
            with open(sshconf_path, 'r') as fp:
                sshconf.parse(fp)
                found = sshconf.lookup(self._hostname)
                self._hostname = found.get('hostname', self._hostname)
                self._port = found.get('port', self._port)
                self._conf_auth_user = found.get('user')
                self._conf_ssh_private_key_file = found.get('identityfile')
            return sshconf_path

    def display_xml_rpc(self, command, format='xml'):
        """
        Executes the CLI command and returns the CLI xml object by default.

        For example::
          print dev.display_xml_rpc('show version').tag
          or
          print dev.display_xml_rpc('show version', format='text')

        :param str command:
          The CLI command to retrieve XML RPC for, e.g. "show version"

        :param str format:
          The return format, by default is XML.  You can optionally select
          "text" to return the XML structure as a string.
        """
        try:
            command = command + '| display xml rpc'
            rsp = self.rpc.cli(command)
            if format == 'text':
                encode = None if sys.version < '3' else 'unicode'
                return etree.tostring(rsp[0], encoding=encode)
            return rsp[0]
        except:
            return "invalid command: " + command

    # ------------------------------------------------------------------------
    # Template: retrieves a Jinja2 template
    # ------------------------------------------------------------------------

    def Template(self, filename, parent=None, gvars=None):
        """
        Used to return a Jinja2 :class:`Template`.

        :param str filename:
            file-path to Jinja2 template file on local device

        :returns: Jinja2 :class:`Template` give **filename**.
        """

        return self._j2ldr.get_template(filename, parent, gvars)

    # ------------------------------------------------------------------------
    # property: manages
    # ------------------------------------------------------------------------

    @property
    def manages(self):
        """
        :returns:
            ``list`` of Resource Managers/Utilities attached to this
            instance using the :meth:`bind` method.
        """
        return self._manages

    # ------------------------------------------------------------------------
    # dealing with bind aspects
    # ------------------------------------------------------------------------

    def bind(self, *vargs, **kvargs):
        """
        Used to attach things to this Device instance and make them a
        property of the :class:Device instance.  The most common use
        for bind is attaching Utility instances to a :class:Device.
        For example::

            from jnpr.junos.utils.config import Config

            dev.bind( cu=Config )
            dev.cu.lock()
            # ... load some changes
            dev.cu.commit()
            dev.cu.unlock()

        :param list vargs:
          A list of functions that will get bound as instance methods to
          this Device instance.

          .. warning:: Experimental.

        :param new_property:
          name/class pairs that will create resource-managers bound as
          instance attributes to this Device instance.  See code example above
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
                if sys.version < '3':
                    self.__dict__[
                        fn.__name__] = types.MethodType(
                        fn,
                        self,
                        self.__class__)
                else:
                    self.__dict__[
                        fn.__name__] = types.MethodType(
                        fn,
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

    @property
    def _sshconf_path(self):
        return self._sshconf_lkup()

    # ------------------------------------------------------------------------
    # probe
    # ------------------------------------------------------------------------

    def probe(self, timeout=5, intvtimeout=1):
        """
        Probe the device to determine if the Device can accept a remote
        connection.
        This method is meant to be called *prior* to :open():
        This method will not work with ssh-jumphost environments.

        :param int timeout:
          The probe will report ``True``/``False`` if the device report
          connectivity within this timeout (seconds)

        :param int intvtimeout:
          Timeout interval on the socket connection. Generally you should not
          change this value, but you can if you want to twiddle the frequency
          of the socket attempts on the connection

        :returns: ``True`` if probe is successful, ``False`` otherwise
        """
        start = datetime.datetime.now()
        end = start + datetime.timedelta(seconds=timeout)
        probe_ok = True

        while datetime.datetime.now() < end:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(intvtimeout)
            try:
                s.connect((self.hostname, int(self._port)))
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

    # ------------------------------------------------------------------------
    # cli - for cheating commands :-)
    # ------------------------------------------------------------------------

    def cli(self, command, format='text', warning=True):
        """
        Executes the CLI command and returns the CLI text output by default.

        :param str command:
          The CLI command to execute, e.g. "show version"

        :param str format:
          The return format, by default is text.  You can optionally select
          "xml" to return the XML structure.

        .. note::
            You can also use this method to obtain the XML RPC command for a
            given CLI command by using the pipe filter ``| display xml rpc``.
            When you do this, the return value is the XML RPC command. For 
            example if you provide as the command ``show version | display xml rpc``,
            you will get back the XML Element ``<get-software-information>``.

        .. warning::
            This function is provided for **DEBUG** purposes only!
            **DO NOT** use this method for general automation purposes as
            that puts you in the realm of "screen-scraping the CLI".  The purpose of
            the PyEZ framework is to migrate away from that tooling pattern.
            Interaction with the device should be done via the RPC function.

        .. warning::
            You cannot use "pipe" filters with **command** such as ``| match``
            or ``| count``, etc.  The only value use of the "pipe" is for the
            ``| display xml rpc`` as noted above.
        """
        if 'display xml rpc' not in command and warning is True:
            warnings.simplefilter("always")
            warnings.warn("CLI command is for debug use only!", RuntimeWarning)
            warnings.resetwarnings()

        try:
            rsp = self.rpc.cli(command, format)
            if isinstance(rsp, dict) and format.lower() == 'json':
                return rsp
            # rsp returned True means <rpc-reply> is empty, hence return
            # empty str as would be the case on cli
            # ex:
            # <rpc-reply message-id="urn:uuid:281f624f-022b-11e6-bfa8">
            # </rpc-reply>
            if rsp is True:
                return ''
            if rsp.tag in ['output', 'rpc-reply']:
                encode = None if sys.version < '3' else 'unicode'
                return etree.tostring(rsp, method="text", with_tail=False,
                                      encoding=encode)
            if rsp.tag == 'configuration-information':
                return rsp.findtext('configuration-output')
            if rsp.tag == 'rpc':
                return rsp[0]
            return rsp
        except EzErrors.RpcError as ex:
            if str(ex) is not '':
                return "%s: %s" % (str(ex), command)
            else:
                return "invalid command: " + command
        except Exception as ex:
            return "invalid command: " + command

    # ------------------------------------------------------------------------
    # execute
    # ------------------------------------------------------------------------

    @normalizeDecorator
    @timeoutDecorator
    def execute(self, rpc_cmd, **kvargs):
        """
        Executes an XML RPC and returns results as either XML or native python

        :param rpc_cmd:
          can either be an XML Element or xml-as-string.  In either case
          the command starts with the specific command element, i.e., not the
          <rpc> element itself

        :param func to_py:
          Is a caller provided function that takes the response and
          will convert the results to native python types.  all kvargs
          will be passed to this function as well in the form::

            to_py( self, rpc_rsp, **kvargs )

        :raises ValueError:
            When the **rpc_cmd** is of unknown origin

        :raises PermissionError:
            When the requested RPC command is not allowed due to
            user-auth class privilege controls on Junos

        :raises RpcError:
            When an ``rpc-error`` element is contained in the RPC-reply

        :returns:
            RPC-reply as XML object.  If **to_py** is provided, then
            that function is called, and return of that function is
            provided back to the caller; presumably to convert the XML to
            native python data-types (e.g. ``dict``).
        """

        if self.connected is not True:
            raise EzErrors.ConnectClosedError(self)

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
            rpc_rsp_e = self._rpc_reply(rpc_cmd_e)
        except NcOpErrors.TimeoutExpiredError:
            # err is a TimeoutExpiredError from ncclient,
            # which has no such attribute as xml.
            raise EzErrors.RpcTimeoutError(self, rpc_cmd_e.tag, self.timeout)
        except NcErrors.TransportError:
            raise EzErrors.ConnectClosedError(self)
        except RPCError as err:
            rsp = JXML.remove_namespaces(err.xml)
            # see if this is a permission error
            e = EzErrors.PermissionError if rsp.findtext('error-message') == \
                'permission denied' \
                else EzErrors.RpcError
            raise e(cmd=rpc_cmd_e, rsp=rsp, errs=err)
        # Something unexpected happened - raise it up
        except Exception as err:
            warnings.warn("An unknown exception occured - please report.",
                          RuntimeWarning)
            raise

        # From 14.2 onward, junos supports JSON, so now code can be written as
        # dev.rpc.get_route_engine_information({'format': 'json'})

        if rpc_cmd_e.attrib.get('format') in ['json', 'JSON']:
            if self._facts == {}:
                self.facts_refresh()
            ver_info = self._facts['version_info']
            if ver_info.major[0] >= 15 or \
                    (ver_info.major[0] == 14 and ver_info.major[1] >= 2):
                try:
                    return json.loads(rpc_rsp_e.text)
                except ValueError as ex:
                    # when data is {}{.*} types
                    if str(ex).startswith('Extra data'):
                        return json.loads(
                            re.sub('\s?{\s?}\s?', '', rpc_rsp_e.text))
            else:
                warnings.warn("Native JSON support is only from 14.2 onwards",
                              RuntimeWarning)

        # This section is here for the possible use of something other than ncclient
        # for RPCs that have embedded rpc-errors, need to check for those now

        # rpc_errs = rpc_rsp_e.xpath('.//rpc-error')
        # if len(rpc_errs):
        #     raise EzErrors.RpcError(cmd=rpc_cmd_e, rsp=rpc_errs[0])

        # skip the <rpc-reply> element and pass the caller first child element
        # generally speaking this is what they really want. If they want to
        # uplevel they can always call the getparent() method on it.

        try:
            ret_rpc_rsp = rpc_rsp_e[0]
        except IndexError:
            # For cases where reply are like
            # <rpc-reply>
            #    protocol: operation-failed
            #    error: device asdf not found
            # </rpc-reply>
            if rpc_rsp_e.text is not None and rpc_rsp_e.text.strip() is not '':
                return rpc_rsp_e
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
    # facts
    # ------------------------------------------------------------------------

    def facts_refresh(self, exception_on_failure=False):
        """
        Reload the facts from the Junos device into :attr:`facts` property.

        :param bool exception_on_failure: To raise exception or warning when
                             facts gathering errors out.

        """
        for gather in FACT_LIST:
            try:
                gather(self, self._facts)
            except:
                if exception_on_failure:
                    raise
                warnings.warn('Facts gathering is incomplete. '
                              'To know the reason call "dev.facts_refresh(exception_on_failure=True)"',
                              RuntimeWarning)
                return


    # -----------------------------------------------------------------------
    # OVERLOADS
    # -----------------------------------------------------------------------

    def __repr__(self):
        return "Device(%s)" % self.hostname


class Device(_Connection):

    """
    Junos Device class.

    :attr:`ON_JUNOS`:
        **READ-ONLY** -
        Auto-set to ``True`` when this code is running on a Junos device,
        vs. running on a local-server remotely connecting to a device.

    :attr:`auto_probe`:
        When non-zero the call to :meth:`open` will probe for NETCONF
        reachability before proceeding with the NETCONF session establishment.
        If you want to enable this behavior by default, you could do the
        following in your code::

            from jnpr.junos import Device

            # set all device open to auto-probe with timeout of 10 sec
            Device.auto_probe = 10

            dev = Device( ... )
            dev.open()   # this will probe before attempting NETCONF connect

    """
    ON_JUNOS = platform.system().upper() == 'JUNOS' or \
        platform.release().startswith('JNPR')
    auto_probe = 0          # default is no auto-probe

    # -------------------------------------------------------------------------
    # PROPERTIES
    # -------------------------------------------------------------------------

    # ------------------------------------------------------------------------
    # property: transform
    # ------------------------------------------------------------------------

    @property
    def transform(self):
        """
        :returns: the current RPC XML Transformation.
        """
        return self._conn._device_handler.transform_reply

    @transform.setter
    def transform(self, func):
        """
        Used to change the RPC XML Transformation.

        :param lambda value:
            New transform lambda
        """
        self._conn._device_handler.transform_reply = func

    # -----------------------------------------------------------------------
    # CONSTRUCTOR
    # -----------------------------------------------------------------------

    def __new__(cls, *args, **kwargs):
        if kwargs.get('port') in [23, '23'] or kwargs.get('mode'):
            from jnpr.junos.console import Console
            instance = object.__new__(Console, *args, **kwargs)
            # Python only calls __init__() if the object returned from
            # __new__() is an instance of the class in which the __new__()
            # method is contained (here Device class). Hence calling __init__
            # explicitly.
            kwargs['host'] = args[0] if len(args) else kwargs.get('host')
            instance.__init__(**kwargs)
            return instance
        else:
            if sys.version < '3':
                return super(Device, cls).__new__(cls, *args, **kwargs)
            else:
                return super().__new__(cls)

    def __init__(self, *vargs, **kvargs):
        """
        Device object constructor.

        :param str vargs[0]: host-name or ipaddress.  This is an
                             alternative for **host**

        :param str host:
            **REQUIRED** host-name or ipaddress of target device

        :param str user:
            *OPTIONAL* login user-name, uses $USER if not provided

        :param str passwd:
            *OPTIONAL* if not provided, assumed ssh-keys are enforced

        :param int port:
            *OPTIONAL* NETCONF port (defaults to 830)

        :param bool gather_facts:
            *OPTIONAL* For ssh mode default is ``True``. In case of console
            connection over telnet/serial it defaults to ``False``.
            If ``False`` then facts are not gathered on call to :meth:`open`

        :param str mode:
            *OPTIONAL*  mode, mode for console connection (telnet/serial)

        :param int baud:
            *OPTIONAL*  baud, Used during serial console mode, default baud
            rate is 9600

        :param int attempts:
            *OPTIONAL*  attempts, for console connection. default is 10

        :param bool auto_probe:
            *OPTIONAL*  if non-zero then this enables auto_probe at time of
            :meth:`open` and defines the amount of time(sec) for the
            probe timeout

        :param str ssh_private_key_file:
            *OPTIONAL* The path to the SSH private key file.
            This can be used if you need to provide a private key rather than
            loading the key into the ssh-key-ring/environment.  if your
            ssh-key requires a password, then you must provide it via
            **passwd**

        :param str ssh_config:
            *OPTIONAL* The path to the SSH configuration file.
            This can be used to load SSH information from a configuration file.
            By default ~/.ssh/config is queried.

        :param bool normalize:
            *OPTIONAL* default is ``False``.  If ``True`` then the
            XML returned by :meth:`execute` will have whitespace normalized
        """

        # ----------------------------------------
        # setup instance connection/open variables
        # ----------------------------------------

        hostname = vargs[0] if len(vargs) else kvargs.get('host')

        self._port = kvargs.get('port', 830)
        self._gather_facts = kvargs.get('gather_facts', True)
        self._normalize = kvargs.get('normalize', False)
        self._auto_probe = kvargs.get('auto_probe', self.__class__.auto_probe)

        if self.__class__.ON_JUNOS is True and hostname is None:
            # ---------------------------------
            # running on a Junos device locally
            # ---------------------------------
            self._auth_user = None
            self._auth_password = None
            self._hostname = 'localhost'
            self._ssh_private_key_file = None
            self._ssh_config = None
        else:
            # --------------------------
            # making a remote connection
            # --------------------------
            if hostname is None:
                raise ValueError("You must provide the 'host' value")
            self._hostname = hostname
            # user will default to $USER
            self._auth_user = os.getenv('USER')
            self._conf_auth_user = None
            self._conf_ssh_private_key_file = None
            # user can get updated by ssh_config
            self._ssh_config = kvargs.get('ssh_config')
            # but if user or private key is explicit from call, then use it.
            self._auth_user = kvargs.get('user') or self._conf_auth_user or \
                self._auth_user
            self._ssh_private_key_file = kvargs.get('ssh_private_key_file') \
                or self._conf_ssh_private_key_file
            self._auth_password = kvargs.get(
                'password') or kvargs.get('passwd')

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
        Opens a connection to the device using existing login/auth
        information.

        :param bool gather_facts:
            If set to ``True``/``False`` will override the device
            instance value for only this open process

        :param bool auto_probe:
            If non-zero then this enables auto_probe and defines the amount
            of time/seconds for the probe timeout

        :param bool normalize:
            If set to ``True``/``False`` will override the device
            instance value for only this open process

        :returns Device: Device instance (*self*).

        :raises ProbeError:
            When **auto_probe** is ``True`` and the probe activity
            exceeds the timeout

        :raises ConnectAuthError:
            When provided authentication credentials fail to login

        :raises ConnectRefusedError:
            When the device does not have NETCONF enabled

        :raises ConnectTimeoutError:
            When the the :meth:`Device.timeout` value is exceeded
            during the attempt to connect to the remote device

        :raises ConnectError:
            When an error, other than the above, occurs.  The
            originating ``Exception`` is assigned as ``err._orig``
            and re-raised to the caller.
        """

        auto_probe = kvargs.get('auto_probe', self._auto_probe)
        if auto_probe is not 0:
            if not self.probe(auto_probe):
                raise EzErrors.ProbeError(self)

        try:
            ts_start = datetime.datetime.now()

            # we want to enable the ssh-agent if-and-only-if we are
            # not given a password or an ssh key file.
            # in this condition it means we want to query the agent
            # for available ssh keys

            allow_agent = bool((self._auth_password is None) and
                               (self._ssh_private_key_file is None))

            # open connection using ncclient transport
            self._conn = netconf_ssh.connect(
                host=self._hostname,
                port=self._port,
                username=self._auth_user,
                password=self._auth_password,
                hostkey_verify=False,
                key_filename=self._ssh_private_key_file,
                allow_agent=allow_agent,
                ssh_config=self._sshconf_lkup(),
                device_params={'name': 'junos', 'local': False})

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

            if str(err).find('not open') > 0:
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

        self._nc_transform = self.transform
        self._norm_transform = lambda: JXML.normalize_xslt.encode('UTF-8')

        normalize = kvargs.get('normalize', self._normalize)
        if normalize is True:
            self.transform = self._norm_transform

        gather_facts = kvargs.get('gather_facts', self._gather_facts)
        if gather_facts is True:
            self.facts_refresh()

        return self

    def close(self):
        """
        Closes the connection to the device.
        """
        self._conn.close_session()
        self.connected = False


    def _rpc_reply(self, rpc_cmd_e):
        return self._conn.rpc(rpc_cmd_e)._NCElement__doc

    # -----------------------------------------------------------------------
    # Context Manager
    # -----------------------------------------------------------------------

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._conn.connected and \
                not isinstance(exc_val, EzErrors.ConnectError):
            self.close()
