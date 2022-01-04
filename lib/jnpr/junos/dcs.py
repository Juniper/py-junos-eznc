"""
This file defines the 'DCS' class.
Used by the 'grpc' connection.
"""
import sys
import logging

# 3rd-party packages
from ncclient.devices.junos import JunosDeviceHandler
from lxml import etree
from ncclient.xml_ import NCElement
from ncclient.operations.rpc import RPCReply, RPCError
from ncclient.xml_ import to_ele

from jnpr.junos.device import _Connection
from jnpr.junos.rpcmeta import _RpcMetaExec
from jnpr.junos.factcache import _FactCache
from jnpr.junos import exception as EzErrors
from jnpr.junos import jxml as JXML

from jnpr.junos.decorators import ignoreWarnDecorator

logger = logging.getLogger("jnpr.junos.dcs")


class DCS(_Connection):
    def __init__(self, **kvargs):
        """
        DCS/EMS object constructor.

        grpc_deps = {
                        "meta_data": meta_data,
                        "stub": css,
                        "uuid": "test1234",
                        "types_pb2": types_pb2,
                        "dcs_pb2": dcs_pb2,
                        "device_info": device_info,
                     }

        :param dict grpc_deps:
            **REQUIRED** gRPC call dependencies
        """

        # ----------------------------------------
        # setup instance connection/open variables
        # ----------------------------------------

        self._tty = None
        self._ofacts = {}
        self.connected = False
        self.results = dict(changed=False, failed=False, errmsg=None)

        self._grpc_deps = kvargs.get("grpc_deps", {})
        self._grpc_conn_stub = self._grpc_deps.get("stub")
        self._grpc_meta_data = self._grpc_deps.get("meta_data", {})
        self._grpc_types_pb2 = self._grpc_deps.get("types_pb2")
        self._grpc_dcs_pb2 = self._grpc_deps.get("dcs_pb2")
        self._dev_uuid = self._grpc_deps.get("uuid")
        self._dev_info = self._grpc_deps.get("device_info")
        self._grpc_timeout = self._grpc_deps.get("grpc_timeout")

        self.junos_dev_handler = JunosDeviceHandler(
            device_params={"name": "junos", "local": False}
        )
        self.rpc = _RpcMetaExec(self)
        self._conn = None
        self.facts = _FactCache(self)
        self._normalize = kvargs.get("normalize", False)
        self._gather_facts = kvargs.get("gather_facts", False)
        self._fact_style = kvargs.get("fact_style", "new")
        self._use_filter = kvargs.get("use_filter", False)

    @property
    def timeout(self):
        """
        :returns: current console connection timeout value (int) in seconds.
        """
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        """
        Used to change the console connection timeout value (default=0.5 sec).

        :param int value:
            New timeout value in seconds
        """
        self._timeout = value

    @property
    def transform(self):
        """
        :returns: the current RPC XML Transformation.
        """
        return self.junos_dev_handler.transform_reply

    @transform.setter
    def transform(self, func):
        """
        Used to change the RPC XML Transformation.

        :param lambda value:
            New transform lambda
        """
        self.junos_dev_handler.transform_reply = func

    def open(self, *vargs, **kvargs):
        """
        Opens a connection to the device using existing login/auth
        information.

        :param bool gather_facts:
            If set to ``True``/``False`` will override the device
            instance value for only this open process
        """

        # for now everything is all connection via gRPC
        self.connected = True

        self._nc_transform = self.transform
        self._norm_transform = lambda: JXML.normalize_xslt.encode("UTF-8")

        self._normalize = kvargs.get("normalize", self._normalize)
        if self._normalize is True:
            self.transform = self._norm_transform

        gather_facts = kvargs.get("gather_facts", self._gather_facts)
        if gather_facts is True:
            logger.info("facts: retrieving device facts...")
            self.facts_refresh()
            self.results["facts"] = self.facts
        self._conn = self._tty
        return self

    def close(self):
        """
        Closes the connection to the device.
        """
        # self._grpc_conn_stub.DisconnectDevice(metadata=self._grpc_meta_data)
        self.connected = False

    @ignoreWarnDecorator
    def _rpc_reply(self, rpc_cmd_e, *args, **kwargs):
        encode = None if sys.version < "3" else "unicode"
        rpc_cmd = (
            etree.tostring(rpc_cmd_e, encoding=encode)
            if isinstance(rpc_cmd_e, etree._Element)
            else rpc_cmd_e
        )
        request_rpc = self._grpc_dcs_pb2.OpRequest(
            command=[rpc_cmd],
            device_info=self._dev_info,
            telemetry=True,
        )
        res = self._grpc_conn_stub.Op(
            request=request_rpc,
            metadata=self._grpc_meta_data,
            timeout=self._grpc_timeout,
        )
        if res.error_code != self._grpc_types_pb2.NoError:
            raise EzErrors.DCSRpcError(
                cmd=rpc_cmd,
                error_code_name=self._grpc_types_pb2.ErrorCode.Name(res.error_code),
                error_code=res.error_code,
                error=res.error,
                uuid=self._dev_uuid,
            )
        result = res.result[0].result
        reply = RPCReply(result)
        errors = reply.errors
        if len(errors) > 1:
            raise RPCError(to_ele(reply._raw), errs=errors)
        elif len(errors) == 1:
            raise reply.error

        rpc_rsp_e = NCElement(
            reply, self.junos_dev_handler.transform_reply()
        )._NCElement__doc
        return rpc_rsp_e

    # -----------------------------------------------------------------------
    # Context Manager
    # -----------------------------------------------------------------------

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connected:
            self.close()
