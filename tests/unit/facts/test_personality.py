__author__ = "Stacy Smith"
__credits__ = "Jeremy Schulman, Nitin Kumar"

import unittest
from nose.plugins.attrib import attr
from mock import patch, MagicMock
import os
from jnpr.junos.exception import RpcError

from jnpr.junos import Device

from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession


@attr("unit")
class TestPersonality(unittest.TestCase):
    @patch("ncclient.manager.connect")
    def setUp(self, mock_connect):
        mock_connect.side_effect = self._mock_manager_setup
        self.dev = Device(
            host="1.1.1.1", user="rick", password="password123", gather_facts=False
        )
        self.dev.open()

    # @patch('jnpr.junos.Device.execute')
    # def test_personality_ex(self, mock_execute):
    #     mock_execute.side_effect = self._mock_manager_personality_ex
    #     self.assertEqual(self.dev.facts['personality'], 'SWITCH')
    #     self.assertEqual(self.dev.facts['virtual'], False)

    @patch("jnpr.junos.Device.execute")
    def test_personality_m(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_personality_m
        self.assertEqual(self.dev.facts["personality"], "M")
        self.assertEqual(self.dev.facts["virtual"], False)

    @patch("jnpr.junos.Device.execute")
    def test_personality_mx(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_personality_mx
        self.assertEqual(self.dev.facts["personality"], "MX")
        self.assertEqual(self.dev.facts["virtual"], False)

    @patch("jnpr.junos.Device.execute")
    def test_personality_olive(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_personality_olive
        self.assertEqual(self.dev.facts["personality"], "OLIVE")
        self.assertEqual(self.dev.facts["virtual"], True)

    @patch("jnpr.junos.Device.execute")
    def test_personality_ptx(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_personality_ptx
        self.assertEqual(self.dev.facts["personality"], "PTX")
        self.assertEqual(self.dev.facts["virtual"], False)

    @patch("jnpr.junos.Device.execute")
    def test_personality_srx_branch(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_personality_srx_branch
        self.assertEqual(self.dev.facts["personality"], "SRX_BRANCH")
        self.assertEqual(self.dev.facts["virtual"], False)

    @patch("jnpr.junos.Device.execute")
    def test_personality_srx_mid_range(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_personality_srx_mid_range
        self.assertEqual(self.dev.facts["personality"], "SRX_MIDRANGE")
        self.assertEqual(self.dev.facts["virtual"], False)

    @patch("jnpr.junos.Device.execute")
    def test_personality_srx_high_end(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_personality_srx_high_end
        self.assertEqual(self.dev.facts["personality"], "SRX_HIGHEND")
        self.assertEqual(self.dev.facts["virtual"], False)

    @patch("jnpr.junos.Device.execute")
    def test_personality_t(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_personality_t
        self.assertEqual(self.dev.facts["personality"], "T")
        self.assertEqual(self.dev.facts["virtual"], False)

    @patch("jnpr.junos.Device.execute")
    def test_personality_vmx(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_personality_vmx
        self.assertEqual(self.dev.facts["personality"], "MX")
        self.assertEqual(self.dev.facts["virtual"], True)

    def test_personality_old_vmx(self):
        self.dev.facts._cache["model"] = "VMX"
        self.assertEqual(self.dev.facts["personality"], "MX")
        self.assertEqual(self.dev.facts["virtual"], True)

    def test_personality_vjx(self):
        self.dev.facts._cache["model"] = "VJX"
        self.assertEqual(self.dev.facts["personality"], "SRX_BRANCH")
        self.assertEqual(self.dev.facts["virtual"], True)

    def test_personality_old_vrr(self):
        self.dev.facts._cache["model"] = "VRR"
        self.assertEqual(self.dev.facts["personality"], "MX")
        self.assertEqual(self.dev.facts["virtual"], True)

    def test_personality_firefly(self):
        self.dev.facts._cache["model"] = "FiReFlY"
        self.assertEqual(self.dev.facts["personality"], "SRX_BRANCH")
        self.assertEqual(self.dev.facts["virtual"], True)

    def test_personality_nfx(self):
        self.dev.facts._cache["model"] = "NFX250_S2_10_T"
        self.assertEqual(self.dev.facts["personality"], "NFX")
        self.assertEqual(self.dev.facts["virtual"], False)

    def test_personality_jdm(self):
        self.dev.facts._cache["model"] = "JUNOS_NODE_SLICING"
        self.assertEqual(self.dev.facts["personality"], "JDM")
        self.assertEqual(self.dev.facts["virtual"], True)

    def test_personality_gnf(self):
        self.dev.facts._cache["model"] = "MX2020"
        self.dev.facts._cache["re_info"] = {
            "default": {"default": {"model": "RE-GNF-2400x4"}}
        }
        self.assertEqual(self.dev.facts["personality"], "MX-GNF")
        self.assertEqual(self.dev.facts["virtual"], True)

    def test_personality_acx(self):
        self.dev.facts._cache["model"] = "ACX7908"
        self.dev.facts._cache["re_info"] = {
            "default": {"default": {"model": "ACX-7900-RE"}}
        }
        self.assertEqual(self.dev.facts["personality"], "ACX")
        self.assertEqual(self.dev.facts["virtual"], False)

    @patch("jnpr.junos.Device.execute")
    def test_personality_vptx(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_personality_vptx
        self.assertEqual(self.dev.facts["personality"], "PTX")
        self.assertEqual(self.dev.facts["virtual"], True)

    def test_personality_virtual_chassis(self):
        self.dev.facts._cache["model"] = "Virtual Chassis"
        self.dev.facts._cache["re_info"] = {
            "default": {"default": {"model": "QFX5100"}}
        }
        self.assertEqual(self.dev.facts["personality"], "SWITCH")
        self.assertEqual(self.dev.facts["virtual"], False)

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

    def _mock_manager_personality_ex(self, *args, **kwargs):
        if args:
            return self._read_file("personality_ex_" + args[0].tag + ".xml")

    def _mock_manager_personality_m(self, *args, **kwargs):
        if args:
            if (
                args[0].tag == "file-show"
                and args[0].xpath("filename")[0].text == "/usr/share/cevo/cevo_version"
            ):
                raise RpcError
            else:
                return self._read_file("personality_m_" + args[0].tag + ".xml")

    def _mock_manager_personality_mx(self, *args, **kwargs):
        if args:
            return self._read_file("personality_mx_" + args[0].tag + ".xml")

    def _mock_manager_personality_olive(self, *args, **kwargs):
        if args:
            return self._read_file("personality_olive_" + args[0].tag + ".xml")

    def _mock_manager_personality_ptx(self, *args, **kwargs):
        if args:
            if (
                args[0].tag == "file-show"
                and args[0].xpath("filename")[0].text == "/usr/share/cevo/cevo_version"
            ):
                raise RpcError
            else:
                return self._read_file("personality_ptx_" + args[0].tag + ".xml")

    def _mock_manager_personality_srx_branch(self, *args, **kwargs):
        if args:
            return self._read_file("personality_srx_branch_" + args[0].tag + ".xml")

    def _mock_manager_personality_srx_high_end(self, *args, **kwargs):
        if args:
            return self._read_file("personality_srx_high_end_" + args[0].tag + ".xml")

    def _mock_manager_personality_srx_mid_range(self, *args, **kwargs):
        if args:
            return self._read_file("personality_srx_mid_range_" + args[0].tag + ".xml")

    def _mock_manager_personality_t(self, *args, **kwargs):
        if args:
            if (
                args[0].tag == "file-show"
                and args[0].xpath("filename")[0].text == "/usr/share/cevo/cevo_version"
            ):
                raise RpcError
            else:
                return self._read_file("personality_t_" + args[0].tag + ".xml")

    def _mock_manager_personality_vmx(self, *args, **kwargs):
        if args:
            return self._read_file("personality_vmx_" + args[0].tag + ".xml")

    def _mock_manager_personality_vptx(self, *args, **kwargs):
        if args:
            return self._read_file("personality_vptx_" + args[0].tag + ".xml")
