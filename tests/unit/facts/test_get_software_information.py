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


class TestGetSoftwareInformation(unittest.TestCase):
    @patch("ncclient.manager.connect")
    def setUp(self, mock_connect):
        mock_connect.side_effect = self._mock_manager_setup
        self.dev = Device(
            host="1.1.1.1", user="rick", password="password123", gather_facts=False
        )
        self.dev.open()

    @patch("jnpr.junos.Device.execute")
    def test_sw_info_single(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_single
        self.assertEqual(self.dev.facts["junos_info"]["re0"]["text"], "16.1R1.11")
        self.assertEqual(
            self.dev.facts["junos_info"]["re0"]["object"].as_tuple,
            (16, 1, "R", "1", 11),
        )
        self.assertEqual(self.dev.facts["hostname"], "r0")
        self.assertEqual(self.dev.facts["model"], "MX960")
        self.assertEqual(self.dev.facts["model_info"], {"re0": "MX960"})
        self.assertEqual(self.dev.facts["version"], "16.1R1.11")
        self.assertEqual(self.dev.facts["version_info"].as_tuple, (16, 1, "R", "1", 11))
        self.assertEqual(self.dev.facts["version_RE0"], "16.1R1.11")
        self.assertEqual(self.dev.facts["version_RE1"], None)

    @patch("jnpr.junos.Device.execute")
    def test_sw_info_vc(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_vc
        self.assertEqual(
            self.dev.facts["junos_info"]["member0"]["text"], "15.1-20161209.0"
        )
        self.assertEqual(
            self.dev.facts["junos_info"]["member0"]["object"].as_tuple,
            (15, 1, "I", "20161209", "0"),
        )
        self.assertEqual(
            self.dev.facts["junos_info"]["member1"]["text"], "15.1-20161209.0"
        )
        self.assertEqual(
            self.dev.facts["junos_info"]["member1"]["object"].as_tuple,
            (15, 1, "I", "20161209", "0"),
        )
        self.assertEqual(self.dev.facts["hostname"], "reefbreak1")
        self.assertEqual(self.dev.facts["model"], "MX240")
        self.assertEqual(
            self.dev.facts["model_info"], {"member1": "MX240", "member0": "MX240"}
        )
        self.assertEqual(self.dev.facts["version"], "15.1-20161209.0")
        self.assertEqual(
            self.dev.facts["version_info"].as_tuple, (15, 1, "I", "20161209", "0")
        )
        self.assertEqual(self.dev.facts["version_RE0"], None)
        self.assertEqual(self.dev.facts["version_RE1"], None)

    @patch("jnpr.junos.Device.execute")
    def test_sw_info_simple(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_simple
        self.assertEqual(self.dev.facts["junos_info"]["re0"]["text"], "12.3X48-D40.5")
        self.assertEqual(
            self.dev.facts["junos_info"]["re0"]["object"].as_tuple,
            (12, 3, "X", (48, "D", 40), 5),
        )
        self.assertEqual(self.dev.facts["hostname"], "lsys500")
        self.assertEqual(self.dev.facts["model"], "SRX3600")
        self.assertEqual(self.dev.facts["model_info"], {"re0": "SRX3600"})
        self.assertEqual(self.dev.facts["version"], "12.3X48-D40.5")
        self.assertEqual(
            self.dev.facts["version_info"].as_tuple, (12, 3, "X", (48, "D", 40), 5)
        )
        self.assertEqual(self.dev.facts["version_RE0"], "12.3X48-D40.5")
        self.assertEqual(self.dev.facts["version_RE1"], None)

    @patch("jnpr.junos.Device.execute")
    def test_sw_info_no_version(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_no_version
        self.assertEqual(self.dev.facts["junos_info"], None)
        self.assertEqual(self.dev.facts["hostname"], "lsys500")
        self.assertEqual(self.dev.facts["model"], "SRX3600")
        self.assertEqual(self.dev.facts["model_info"], {"re0": "SRX3600"})
        self.assertEqual(self.dev.facts["version"], "0.0I0.0")
        self.assertEqual(self.dev.facts["version_RE0"], None)
        self.assertEqual(self.dev.facts["version_RE1"], None)

    @patch("jnpr.junos.Device.execute")
    def test_sw_info_dual(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_dual
        self.assertEqual(self.dev.facts["junos_info"]["re0"]["text"], "15.1F5.15-C1.12")
        self.assertEqual(self.dev.facts["junos_info"]["re1"]["text"], "15.1F5.15")
        self.assertEqual(self.dev.facts["hostname"], "baku")
        self.assertEqual(self.dev.facts["model"], "MX480")
        self.assertEqual(self.dev.facts["model_info"], {"re0": "MX480", "re1": "MX480"})
        self.assertEqual(self.dev.facts["version"], "15.1F5.15-C1.12")
        self.assertEqual(self.dev.facts["version_RE0"], "15.1F5.15-C1.12")
        self.assertEqual(self.dev.facts["version_RE1"], "15.1F5.15")

    @patch("jnpr.junos.Device.execute")
    def test_sw_info_dual_other_re_off(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_dual_other_re_off
        self.assertEqual(
            self.dev.facts["junos_info"]["re1"]["text"], "18.3I20180716_1639"
        )
        self.assertEqual(self.dev.facts["hostname"], "R1_re01")
        self.assertEqual(self.dev.facts["model"], "MX960")
        self.assertEqual(self.dev.facts["model_info"], {"re1": "MX960"})
        self.assertEqual(self.dev.facts["version"], "18.3I20180716_1639")
        self.assertEqual(self.dev.facts["version_RE1"], "18.3I20180716_1639")

    @patch("jnpr.junos.Device.execute")
    def test_sw_info_txp(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_txp
        self.assertEqual(self.dev.facts["junos_info"]["re0"]["text"], "13.3R9-S2.1")
        self.assertEqual(self.dev.facts["hostname"], "dj")
        self.assertEqual(self.dev.facts["model"], "T1600")
        self.assertEqual(self.dev.facts["model_info"], {"re0": "T1600"})
        self.assertEqual(self.dev.facts["version"], "13.3R9-S2.1")
        self.assertEqual(self.dev.facts["version_RE0"], "13.3R9-S2.1")
        self.assertEqual(self.dev.facts["version_RE1"], None)

    @patch("jnpr.junos.Device.execute")
    def test_sw_info_ex(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_ex
        self.assertEqual(self.dev.facts["junos_info"]["re0"]["text"], "11.4R1.6")
        self.assertEqual(self.dev.facts["hostname"], "sw1")
        self.assertEqual(self.dev.facts["model"], "EX2200-C-12T-2G")
        self.assertEqual(self.dev.facts["model_info"], {"re0": "EX2200-C-12T-2G"})
        self.assertEqual(self.dev.facts["version"], "11.4R1.6")
        self.assertEqual(self.dev.facts["version_RE0"], "11.4R1.6")
        self.assertEqual(self.dev.facts["version_RE1"], None)

    @patch("jnpr.junos.Device.execute")
    def test_sw_info_nfx(self, mock_execute):
        self.dev.facts._cache["vc_capable"] = False
        mock_execute.side_effect = self._mock_manager_nfx
        self.assertEqual(self.dev.facts["hostname"], "jdm")
        self.assertEqual(self.dev.facts["model"], "NFX250_S2_10_T")
        self.assertEqual(self.dev.facts["version"], "15.1X53-D45.3")
        self.assertEqual(self.dev.facts["version_RE0"], "15.1X53-D45.3")
        self.assertEqual(self.dev.facts["version_RE1"], None)
        self.assertEqual(self.dev.facts["model_info"], {"re0": "NFX250_S2_10_T"})
        self.assertEqual(self.dev.facts["junos_info"]["re0"]["text"], "15.1X53-D45.3")

    @patch("jnpr.junos.Device.execute")
    def test_sw_info_bsys(self, mock_execute):
        self.dev.facts._cache["current_re"] = [
            "master",
            "node",
            "fwdd",
            "member",
            "pfem",
            "re0",
        ]
        self.dev.facts._cache["vc_capable"] = False
        mock_execute.side_effect = self._mock_manager_bsys
        self.assertEqual(self.dev.facts["hostname"], "bsys")
        self.assertEqual(self.dev.facts["model"], "MX2020")
        self.assertEqual(self.dev.facts["version"], "17.4-20170706_dev_common.0")
        self.assertEqual(self.dev.facts["version_RE0"], "17.4-20170706_dev_common.0")
        self.assertEqual(self.dev.facts["version_RE1"], "17.4-20170706_dev_common.0")
        self.assertEqual(
            self.dev.facts["model_info"],
            {
                "bsys-re0": "MX2020",
                "bsys-re1": "MX2020",
                "gnf1-re0": "MX2020",
                "gnf1-re1": "MX2020",
                "gnf2-re0": "MX2020",
                "gnf2-re1": "MX2020",
                "gnf3-re0": "MX2020",
                "gnf3-re1": "MX2020",
                "gnf4-re0": "MX2020",
                "gnf4-re1": "MX2020",
            },
        )
        self.assertEqual(
            self.dev.facts["junos_info"]["bsys-re0"]["text"],
            "17.4-20170706_dev_common.0",
        )

    @patch("jnpr.junos.Device.execute")
    def test_sw_info_jdm(self, mock_execute):
        self.dev.facts._cache["vc_capable"] = False
        self.dev.facts._cache["current_re"] = ["server0"]
        mock_execute.side_effect = self._mock_manager_jdm
        self.assertEqual(self.dev.facts["hostname"], "jdm")
        self.assertEqual(self.dev.facts["model"], "JUNOS_NODE_SLICING")
        self.assertEqual(self.dev.facts["version"], "17.4-20170718_dev_common.1-secure")
        self.assertEqual(
            self.dev.facts["version_RE0"], "17.4-20170718_dev_common.1-secure"
        )
        self.assertEqual(
            self.dev.facts["version_RE1"], "17.4-20170718_dev_common.1-secure"
        )
        self.assertEqual(
            self.dev.facts["model_info"],
            {"server0": "JUNOS_NODE_SLICING", "server1": "JUNOS_NODE_SLICING"},
        )
        self.assertEqual(
            self.dev.facts["junos_info"]["server0"]["text"],
            "17.4-20170718_dev_common.1-secure",
        )
        self.assertEqual(
            self.dev.facts["junos_info"]["server1"]["text"],
            "17.4-20170718_dev_common.1-secure",
        )

    @patch("jnpr.junos.Device.execute")
    def test_sw_info_gnf(self, mock_execute):
        self.dev.facts._cache["vc_capable"] = False
        self.dev.facts._cache["current_re"] = ["gnf7-master", "gnf7-re0"]
        mock_execute.side_effect = self._mock_manager_gnf
        self.assertEqual(self.dev.facts["hostname"], "mgb-gnf-a")
        self.assertEqual(self.dev.facts["model"], "MX960")
        self.assertEqual(self.dev.facts["version"], "18.4-20180707_dev_common.0")
        self.assertEqual(self.dev.facts["version_RE0"], "18.4-20180707_dev_common.0")
        self.assertEqual(self.dev.facts["version_RE1"], "18.4-20180707_dev_common.0")
        self.assertEqual(
            self.dev.facts["model_info"],
            {
                "bsys-re0": "MX960",
                "bsys-re1": "MX960",
                "gnf7-re0": "MX960",
                "gnf7-re1": "MX960",
            },
        )
        self.assertEqual(
            self.dev.facts["junos_info"]["gnf7-re0"]["text"],
            "18.4-20180707_dev_common.0",
        )
        self.assertEqual(
            self.dev.facts["junos_info"]["gnf7-re1"]["text"],
            "18.4-20180707_dev_common.0",
        )

    @patch("jnpr.junos.Device.execute")
    def test_sw_info_srx_cluster(self, mock_execute):
        self.dev.facts._cache["vc_capable"] = False
        self.dev.facts._cache["current_re"] = ["node0"]
        mock_execute.side_effect = self._mock_manager_srx_cluster
        self.assertEqual(self.dev.facts["hostname"], "frogbert")
        self.assertEqual(self.dev.facts["model"], "SRX5800")
        self.assertEqual(
            self.dev.facts["version"], "17.3-2017-07-02.0_RELEASE_173_THROTTLE"
        )
        self.assertEqual(
            self.dev.facts["version_RE0"], "17.3-2017-07-02.0_RELEASE_173_THROTTLE"
        )
        self.assertEqual(
            self.dev.facts["version_RE1"], "17.3-2017-07-02.0_RELEASE_173_THROTTLE"
        )
        self.assertEqual(
            self.dev.facts["model_info"], {"node0": "SRX5800", "node1": "SRX5800"}
        )
        self.assertEqual(
            self.dev.facts["junos_info"]["node0"]["text"],
            "17.3-2017-07-02.0_RELEASE_173_THROTTLE",
        )
        self.assertEqual(
            self.dev.facts["junos_info"]["node1"]["text"],
            "17.3-2017-07-02.0_RELEASE_173_THROTTLE",
        )

    @patch("jnpr.junos.Device.execute")
    def test_sw_info_err(self, mock_execute):
        self.dev.facts._cache["vc_capable"] = False
        self.dev.facts._cache["current_re"] = None
        mock_execute.side_effect = self._mock_manager_err
        self.assertEqual(self.dev.facts["hostname"], None)
        self.assertEqual(self.dev.facts["model"], None)
        self.assertEqual(self.dev.facts["version"], None)
        self.assertEqual(self.dev.facts["version_RE0"], None)
        self.assertEqual(self.dev.facts["version_RE1"], None)
        self.assertEqual(self.dev.facts["model_info"], None)
        self.assertEqual(self.dev.facts["junos_info"], None)

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

    def _mock_manager_single(self, *args, **kwargs):
        if args:
            return self._read_file("sw_info_single_" + args[0].tag + ".xml")

    def _mock_manager_vc(self, *args, **kwargs):
        if args:
            if (
                args[0].tag == "command"
                and args[0].text == "show version invoke-on all-routing-engines"
            ):
                raise RpcError()
            elif (
                args[0].tag == "file-show"
                and args[0].xpath("filename")[0].text == "/usr/share/cevo/cevo_version"
            ):
                raise RpcError
            else:
                return self._read_file("sw_info_vc_" + args[0].tag + ".xml")

    def _mock_manager_simple(self, *args, **kwargs):
        if args:
            if args[0].tag == "command":
                raise RpcError()
            else:
                return self._read_file("sw_info_simple_" + args[0].tag + ".xml")

    def _mock_manager_no_version(self, *args, **kwargs):
        if args:
            if args[0].tag == "command":
                raise RpcError()
            else:
                return self._read_file("sw_info_no_version_" + args[0].tag + ".xml")

    def _mock_manager_dual(self, *args, **kwargs):
        if args:
            if (
                args[0].tag == "file-show"
                and args[0].xpath("filename")[0].text == "/usr/share/cevo/cevo_version"
            ):
                raise RpcError
            else:
                return self._read_file("sw_info_dual_" + args[0].tag + ".xml")

    def _mock_manager_dual_other_re_off(self, *args, **kwargs):
        if args:
            return self._read_file("sw_info_dual_other_re_off.xml").getparent()

    def _mock_manager_txp(self, *args, **kwargs):
        if args:
            if args[0].tag == "command":
                raise RpcError()
            else:
                return self._read_file("sw_info_txp_" + args[0].tag + ".xml")

    def _mock_manager_ex(self, *args, **kwargs):
        if args:
            if args[0].tag == "command":
                raise RpcError()
            else:
                return self._read_file("sw_info_ex_" + args[0].tag + ".xml")

    def _mock_manager_nfx(self, *args, **kwargs):
        if args:
            if args[0].tag == "command":
                raise RpcError()
            elif (
                args[0].tag == "get-software-information"
                and args[0].find("./*") is None
            ):
                return True
            else:
                return self._read_file("sw_info_nfx_" + args[0].tag + ".xml")

    def _mock_manager_bsys(self, *args, **kwargs):
        if args:
            if args[0].tag == "command":
                raise RpcError()
            elif (
                args[0].tag == "get-software-information"
                and args[0].find("./*") is None
            ):
                return True
            else:
                return self._read_file("sw_info_bsys_" + args[0].tag + ".xml")

    def _mock_manager_srx_cluster(self, *args, **kwargs):
        if args:
            if args[0].tag == "command":
                raise RpcError()
            else:
                return self._read_file("sw_info_srx_cluster_" + args[0].tag + ".xml")

    def _mock_manager_jdm(self, *args, **kwargs):
        if args:
            if args[0].tag == "command":
                if args[0].text == "show version invoke-on all-routing-engines":
                    raise RpcError()
                else:
                    return self._read_file(
                        "sw_info_jdm_command_" + args[0].text + ".xml"
                    )
            else:
                return self._read_file("sw_info_jdm_" + args[0].tag + ".xml")

    def _mock_manager_gnf(self, *args, **kwargs):
        if args:
            if args[0].tag == "command":
                raise RpcError()
            elif (
                args[0].tag == "get-software-information"
                and args[0].find("./*") is None
            ):
                return True
            else:
                return self._read_file("sw_info_gnf_" + args[0].tag + ".xml")

    def _mock_manager_err(self, *args, **kwargs):
        if args:
            raise RpcError()
