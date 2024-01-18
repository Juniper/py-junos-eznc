__author__ = "Stacy Smith"
__credits__ = "Jeremy Schulman, Nitin Kumar"

import unittest
import nose2
from mock import patch, MagicMock
import os
from lxml import etree

from jnpr.junos import Device
from jnpr.junos.exception import RpcError

from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession


class TestCurrentRe(unittest.TestCase):
    @patch("ncclient.manager.connect")
    def setUp(self, mock_connect):
        mock_connect.side_effect = self._mock_manager_setup
        self.dev = Device(
            host="1.1.1.1", user="rick", password="password123", gather_facts=False
        )
        self.dev.open()

    @patch("jnpr.junos.Device.execute")
    def test_current_re_fact(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_current_re
        self.assertEqual(
            self.dev.facts["current_re"],
            ["re0", "master", "node", "fwdd", "member", "pfem"],
        )

    @patch("jnpr.junos.Device.execute")
    def test_current_re_fact_empty(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_current_re_empty
        self.assertEqual(self.dev.facts["current_re"], None)

    @patch("jnpr.junos.Device.execute")
    def test_current_re_fact_srx_cluster_primary(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_current_re_srx_primary
        self.dev.facts._cache["srx_cluster_id"] = "15"
        self.assertEqual(self.dev.facts["current_re"], ["node0", "primary"])

    @patch("jnpr.junos.Device.execute")
    def test_current_re_fact_srx_cluster_primary_id_255(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_current_re_srx_primary
        self.dev.facts._cache["srx_cluster_id"] = "255"
        self.assertEqual(self.dev.facts["current_re"], ["node0", "primary"])

    @patch("jnpr.junos.Device.execute")
    def test_current_re_fact_srx_cluster_primary_id_16(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_current_re_srx_primary
        self.dev.facts._cache["srx_cluster_id"] = "16"
        print(self.dev.facts._cache["srx_cluster_id"])
        self.assertEqual(self.dev.facts["current_re"], ["node0"])

    @patch("jnpr.junos.Device.execute")
    def test_current_re_fact_srx_cluster_primary_id_31(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_current_re_srx_primary
        self.dev.facts._cache["srx_cluster_id"] = "31"
        self.assertEqual(self.dev.facts["current_re"], ["node0", "primary"])

    @patch("jnpr.junos.Device.execute")
    def test_current_re_fact_srx_cluster_secondary(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_current_re_srx_secondary
        self.dev.facts._cache["srx_cluster_id"] = "15"
        self.assertEqual(self.dev.facts["current_re"], ["node1"])

    @patch("jnpr.junos.Device.execute")
    def test_current_re_fact_srx_cluster_index_error(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_current_re_srx_index_err
        self.dev.facts._cache["srx_cluster_id"] = "15"
        self.assertEqual(self.dev.facts["current_re"], None)

    @patch("jnpr.junos.Device.execute")
    def test_current_re_fact_jdm(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_current_re_jdm
        self.assertEqual(self.dev.facts["current_re"], ["server0"])

    @patch("jnpr.junos.Device.execute")
    def test_current_re_fact_rpc_error(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_current_re_rpc_error
        self.assertEqual(self.dev.facts["current_re"], None)

    def _read_file(self, fname):
        from ncclient.xml_ import NCElement

        fpath = os.path.join(os.path.dirname(__file__), "rpc-reply", fname)
        foo = open(fpath).read()

        rpc_reply = NCElement(
            foo, self.dev._conn._device_handler.transform_reply()
        )._NCElement__doc[0]
        return rpc_reply

    def _mock_manager_setup(self, *args, **kwargs):
        if kwargs:
            device_params = kwargs["device_params"]
            device_handler = make_device_handler(device_params)
            session = SSHSession(device_handler)
            return Manager(session, device_handler)

    def _mock_manager_current_re(self, *args, **kwargs):
        if args:
            if (
                args[0].tag == "file-show"
                and args[0].xpath("filename")[0].text == "/usr/share/cevo/cevo_version"
            ):
                raise RpcError
            else:
                return self._read_file("current_re_" + args[0].tag + ".xml")

    def _mock_manager_current_re_empty(self, *args, **kwargs):
        if args:
            if (
                args[0].tag == "file-show"
                and args[0].xpath("filename")[0].text == "/usr/share/cevo/cevo_version"
            ):
                raise RpcError
            else:
                return self._read_file("current_re_empty_" + args[0].tag + ".xml")

    def _mock_manager_current_re_srx_primary(self, *args, **kwargs):
        if args:
            if (
                args[0].tag == "file-show"
                and args[0].xpath("filename")[0].text == "/usr/share/cevo/cevo_version"
            ):
                raise RpcError
            else:
                return self._read_file("current_re_srx_primary_" + args[0].tag + ".xml")

    def _mock_manager_current_re_srx_secondary(self, *args, **kwargs):
        if args:
            if (
                args[0].tag == "file-show"
                and args[0].xpath("filename")[0].text == "/usr/share/cevo/cevo_version"
            ):
                raise RpcError
            else:
                return self._read_file(
                    "current_re_srx_secondary_" + args[0].tag + ".xml"
                )

    def _mock_manager_current_re_srx_index_err(self, *args, **kwargs):
        if args:
            if (
                args[0].tag == "file-show"
                and args[0].xpath("filename")[0].text == "/usr/share/cevo/cevo_version"
            ):
                raise RpcError
            else:
                return self._read_file(
                    "current_re_srx_index_err_" + args[0].tag + ".xml"
                )

    def _mock_manager_current_re_jdm(self, *args, **kwargs):
        if args:
            if (
                args[0].tag == "file-show"
                and args[0].xpath("filename")[0].text == "/usr/share/cevo/cevo_version"
            ):
                raise RpcError
            elif args[0].tag == "get-interface-information":
                raise RpcError()
            else:
                return self._read_file("current_re_jdm_" + args[0].tag + ".xml")

    def _mock_manager_current_re_rpc_error(self, *args, **kwargs):
        if args:
            raise RpcError()
