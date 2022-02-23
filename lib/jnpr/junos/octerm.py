"""
This file defines the 'OCTerm' class.
This has the functionality to communicate to oc-terminator of JCloud over kafka
"""
import json
import sys
import logging

# 3rd-party packages
import time

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
from confluent_kafka import  KafkaError, KafkaException

logger = logging.getLogger("jnpr.junos.octerm")


class OCTerm(_Connection):
    def __init__(self, uuid, producer, consumer, id, **kvargs):
        """
        OCTerm object constructor.

        grpc_deps = {
                        "meta_data": meta_data,
                        "stub": css,
                        "uuid": "test1234",
                        "types_pb2": types_pb2,
                        "dcs_pb2": dcs_pb2,
                        "device_info": device_info,
                     }

        :param dict kvargs:
            **REQUIRED** gRPC call dependencies
        """

        # ----------------------------------------
        # setup instance connection/open variables
        # ----------------------------------------

        self._tty = None
        self._ofacts = {}
        self.connected = False
        self.results = dict(changed=False, failed=False, errmsg=None)
        self._hostname = "hostname"
        self._dev_uuid = uuid

        # self._grpc_deps = kvargs.get("grpc_deps", {})
        # self._grpc_conn_stub = self._grpc_deps.get("stub")
        # self._grpc_meta_data = self._grpc_deps.get("meta_data", {})
        # self._grpc_types_pb2 = self._grpc_deps.get("types_pb2")
        # self._grpc_dcs_pb2 = self._grpc_deps.get("dcs_pb2")
        # self._dev_uuid = self._grpc_deps.get("uuid")
        # self._dev_info = self._grpc_deps.get("device_info")
        # self._grpc_timeout = self._grpc_deps.get("grpc_timeout")
        self._producer = producer
        self._consumer = consumer
        self._id = id

        if self._producer is None or self._consumer is None:
            raise Exception("produce/consumer should be initialized")

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
        rpc_cmd.encode("unicode_escape")
        kafka_cmd = {
            "op": "OC_COMMAND",
            "command": "netconf-rpc",
            "requestID": self._dev_uuid + ":" + rpc_cmd + ":" + self._id + str(time.time()),
            "resource": self._dev_uuid,
            "id": self._dev_uuid,
            "params": rpc_cmd,
            "netconfCommand": rpc_cmd
        }
        result = ""
        self._producer.produce(
            "oc-cmd-dev", key="key", value=json.dumps(kafka_cmd))
        time_start = time.time()
        while True:
            if time.time() - time_start >= self.timeout:
                raise EzErrors.OCTermRpcError(
                    cmd=rpc_cmd,
                    error="Timeout waiting for response",
                    uuid=self._dev_uuid,
                )
            msg = self._consumer.poll(timeout=5)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition event
                    continue
                elif msg.error():
                    raise KafkaException(msg.error())
            else:
                self._consumer.commit(asynchronous=False)
                resp = json.loads(msg.value())
                if resp.get("requestID", "") == kafka_cmd["requestID"]:
                    if "Payload" in resp and "Output" in resp["Payload"]:
                        result = resp["Payload"]["Output"]
                        break
                    else:
                        raise EzErrors.OCTermRpcError(
                            cmd=rpc_cmd,
                            error=resp.get("Payload", {}).get(
                                "Error", "Unknown error"),
                            uuid=self._dev_uuid,
                        )
                else:
                    print("============")

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
