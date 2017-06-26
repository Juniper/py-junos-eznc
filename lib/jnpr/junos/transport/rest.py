import sys
import logging
import requests
import warnings

# 3rd-party packages
from ncclient.devices.junos import JunosDeviceHandler
from lxml import etree
from ncclient.xml_ import NCElement
from jnpr.junos.device import _Connection
from ncclient import manager
from ncclient.operations.rpc import RPCReply, RPCError
import ncclient.operations.errors as NcOpErrors
import ncclient.transport.errors as NcErrors

# local modules
from jnpr.junos.rpcmeta import _RpcMetaExec
from jnpr.junos.factcache import _FactCache
from jnpr.junos import jxml as JXML
from jnpr.junos import exception as EzErrors
from jnpr.junos.ofacts import *
from jnpr.junos.decorators import timeoutDecorator, normalizeDecorator, \
    ignoreWarnDecorator

logger = logging.getLogger("jnpr.junos.rest")

# -------------------------------------------------------------------------
# Rest
# -------------------------------------------------------------------------

class Rest():

    def __init__(self, **kvargs):
        self._device_handler = manager.make_device_handler(None)

        self._tty = None
        self._ofacts = {}
        self.connected = False
        self._skip_logout = True
        self.results = dict(changed=False, failed=False, errmsg=None)

        self._hostname = kvargs.get('host')
        self._schema = kvargs.get('schema', 'https')
        self._path = kvargs.get('path', '/rpc')
        self.dev = kvargs.get('dev', None)
        self._ssl_verify = kvargs.get('ssl_verify', True)
        self._auth_user = kvargs.get('user', 'root')
        self._auth_password = kvargs.get(
            'password',
            '') or kvargs.get(
            'passwd',
            '')
        self._port = kvargs.get('port', '443')
        self._mode = kvargs.get('mode', 'rest')
        self._timeout = kvargs.get('timeout', '5')
        self._normalize = kvargs.get('normalize', False)

        self._attempts = kvargs.get('attempts', 10)
        self._gather_facts = kvargs.get('gather_facts', False)
        self._fact_style = kvargs.get('fact_style', 'new')
        if self._fact_style != 'new':
            warnings.warn('fact-style %s will be removed in '
                          'a future release.' %
                          (self._fact_style), RuntimeWarning)

        self.rpc = _RpcMetaExec(self)
        self._manages = []
        self.junos_dev_handler = JunosDeviceHandler(
                                     device_params={'name': 'junos',
                                                    'local': False})
        if self._fact_style == 'old':
            self.facts = self.ofacts
        else:
            self.facts = _FactCache(self)

    def open(self, *vargs, **kvargs):
        gather_facts = kvargs.get('gather_facts', self._gather_facts)
        if gather_facts is True:
            logger.info('facts: retrieving device facts...')
            self.facts_refresh()
            self.results['facts'] = self.facts
        return self

    def close_session(self):
        return True

    def close(self, skip_logout=True):
        pass

    @ignoreWarnDecorator
    def _rpc_reply(self, rpc_cmd_e):
        encode = None if sys.version < '3' else 'unicode'
        rpc_cmd = etree.tostring(rpc_cmd_e, encoding=encode) \
            if isinstance(rpc_cmd_e, etree._Element) else rpc_cmd_e
        try:
            reply = self._rpc_query(rpc_cmd)
        except requests.exceptions.HTTPError as e:
            logger.error('HTTP error: {}'.format(e))
            raise EzErrors.ConnectError(self.dev, e)
        except requests.exceptions.ConnectTimeout as e:
            logger.error('ConnectTimeout error: {}'.format(e))
            raise EzErrors.ConnectError(self.dev, e)
        rpc_rsp_e = NCElement(reply,
              self.junos_dev_handler.transform_reply()
              )
        return rpc_rsp_e

    def _parse_multipart(self, boundary, payload):
        lines = payload.split('\n')
        extracted = []
        enable_capture = False
        enable_parsing = False
        for line in lines:
            # Parsing the HTTP query result.
            # Delimiters are the boundaries.
            # The position of the dashes indicates if beginning or end.
            if '--'+boundary == line:
                enable_capture = True
                extracted.append([])
            elif '--'+boundary+'--' == line:
                enable_capture = False
                enable_parsing = False
            elif enable_capture:
                if line == '':
                    enable_parsing = True
                elif enable_parsing:
                    extracted[len(extracted)-1].append(line)
        extracted_join = []
        for extract in extracted:
            extracted_join.append("\n".join(extract))
        return extracted_join

    def _parse_headers(self, headers):
        content_type = headers.get('Content-Type', '')
        content_type_value = content_type.split('; ')
        for kv in content_type_value:
            kv_list = kv.split('=')
            if kv_list[0] == 'boundary':
                return kv_list[1]
        return None

    def _rpc_query(self, cmd):
        reply = requests.post('{}://{}:{}{}'.format(self._schema, self._hostname, self._port, self._path),
            data = cmd,
            auth = (self._auth_user, self._auth_password),
            verify = self._ssl_verify,
            timeout = float(self._timeout),
            headers={'Accept': 'application/xml', 'Content-Type': 'application/xml'})
        reply.raise_for_status()
        boundary = self._parse_headers(reply.headers)
        parsed = self._parse_multipart(boundary, reply.text)

        if reply.ok:
            self.connected = True

        # Queries done using HTTP REST do not provide the RPC reply tag the NCElement expects.
        return '<rpc-reply>{document}</rpc-reply>'.format(document=parsed[0])

    # ------------------------------------------------------------------------
    # execute
    # ------------------------------------------------------------------------

    @normalizeDecorator
    @timeoutDecorator
    def execute(self, rpc_cmd, ignore_warning=False, **kvargs):
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
            rpc_rsp_e = self._rpc_reply(rpc_cmd_e,
                                        ignore_warning=ignore_warning)
        except NcOpErrors.TimeoutExpiredError:
            # err is a TimeoutExpiredError from ncclient,
            # which has no such attribute as xml.
            raise EzErrors.RpcTimeoutError(self, rpc_cmd_e.tag, self.timeout)
        except NcErrors.TransportError:
            raise EzErrors.ConnectClosedError(self)
        except RPCError as ex:
            if hasattr(ex, 'xml'):
                rsp = JXML.remove_namespaces(ex.xml)
                message = rsp.findtext('error-message')
                # see if this is a permission error
                if message and message == 'permission denied':
                    raise EzErrors.PermissionError(cmd=rpc_cmd_e,
                                                   rsp=rsp,
                                                   errs=ex)
            else:
                rsp = None
            raise EzErrors.RpcError(cmd=rpc_cmd_e,
                                    rsp=rsp,
                                    errs=ex)
        # Something unexpected happened - raise it up
        except Exception as err:
            warnings.warn("An unknown exception occured - please report.",
                          RuntimeWarning)
            raise

        if kvargs.get('to_py'):
            return kvargs['to_py'](self, rpc_rsp_e, **kvargs)
        else:
            return rpc_rsp_e

