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


class TestEthernetMacTable(unittest.TestCase):
    @patch("ncclient.manager.connect")
    def setUp(self, mock_connect):
        mock_connect.side_effect = self._mock_manager_setup
        self.dev = Device(
            host="1.1.1.1", user="rick", password="password123", gather_facts=False
        )
        self.dev.open()

    @patch("jnpr.junos.Device.execute")
    def test_ethernet_mac_table_els(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_els
        self.assertEqual(self.dev.facts["switch_style"], "VLAN_L2NG")

    @patch("jnpr.junos.Device.execute")
    def test_ethernet_mac_table_vlan(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_vlan
        self.assertEqual(self.dev.facts["switch_style"], "VLAN")

    @patch("jnpr.junos.Device.execute")
    def test_ethernet_mac_table_bd(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_bd
        self.assertEqual(self.dev.facts["switch_style"], "BRIDGE_DOMAIN")

    @patch("jnpr.junos.Device.execute")
    def test_ethernet_mac_table_none(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_none
        self.assertEqual(self.dev.facts["switch_style"], "NONE")

    @patch("jnpr.junos.Device.execute")
    def test_ethernet_mac_table_non_master_bd_ptx(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_ptx
        self.assertEqual(self.dev.facts["switch_style"], "NONE")

    @patch("jnpr.junos.Device.execute")
    def test_ethernet_mac_table_non_master_bd_mx(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_mx_non_master_re
        self.assertEqual(self.dev.facts["switch_style"], "BRIDGE_DOMAIN")

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

    def _mock_manager_els(self, *args, **kwargs):
        if args:
            return self._read_file("els_" + args[0].tag + ".xml")

    def _mock_manager_vlan(self, *args, **kwargs):
        if args:
            return self._read_file("vlan_" + args[0].tag + ".xml")

    def _mock_manager_bd(self, *args, **kwargs):
        if args:
            if args[0].tag == "get-ethernet-switching-table-information":
                raise RpcError()
            else:
                return self._read_file("bd_" + args[0].tag + ".xml")

    def _mock_manager_none(self, *args, **kwargs):
        if args:
            if args[0].tag == "get-ethernet-switching-table-information":
                raise RpcError()
            else:
                return self._read_file("switch_style_none_" + args[0].tag + ".xml")

    def _mock_manager_mx_non_master_re(self, *args, **kwargs):
        if args:
            if args[0].tag == "get-ethernet-switching-table-information":
                raise RpcError()
            elif args[0].tag == "command":
                xml = """
                    <xnm:error xmlns="http://xml.juniper.net/xnm/1.1/xnm" xmlns:xnm="http://xml.juniper.net/xnm/1.1/xnm">
                        <message>the l2-learning subsystem is not running</message>
                        <reason>
                            <daemon>l2-learning</daemon>
                            <process-not-running/>
                        </reason>
                    </xnm:error>
                """
                rsp = etree.XML(xml)
                err = RpcError(rsp=rsp)
                err.rpc_error["bad_element"] = "none"
                err.rpc_error["message"] = "the l2-learning subsystem is not running"
                raise err
            else:
                return None

    def _mock_manager_ptx(self, *args, **kwargs):
        if args:
            if args[0].tag == "get-ethernet-switching-table-information":
                raise RpcError()
            elif args[0].tag == "command":
                xml = """
                    <rpc-error>
                        <error-type>protocol</error-type>
                        <error-tag>operation-failed</error-tag>
                        <error-severity>error</error-severity>
                        <error-message>syntax error, expecting &lt;command&gt;</error-message>
                        <error-info>
                            <bad-element>bridge</bad-element>
                        </error-info>
                    </rpc-error>
                """
                rsp = etree.XML(xml)
                err = RpcError(rsp=rsp)
                err.rpc_error["bad_element"] = "bridge"
                raise err
            else:
                return None
