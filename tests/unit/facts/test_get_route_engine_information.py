__author__ = "Stacy Smith"
__credits__ = "Jeremy Schulman, Nitin Kumar"

import unittest
import nose2
from mock import patch, MagicMock
import os
from lxml import etree

from jnpr.junos import Device

from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession


class TestGetRouteEngineInformation(unittest.TestCase):
    @patch("ncclient.manager.connect")
    def setUp(self, mock_connect):
        mock_connect.side_effect = self._mock_manager_setup
        self.dev = Device(
            host="1.1.1.1", user="rick", password="password123", gather_facts=False
        )
        self.dev.open()

    @patch("jnpr.junos.Device.execute")
    def test_re_info_dual(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_dual_re
        self.assertEqual(self.dev.facts["2RE"], True)
        self.assertEqual(self.dev.facts["master"], "RE0")
        self.assertEqual(
            self.dev.facts["RE0"],
            {
                "status": "OK",
                "last_reboot_reason": "Router rebooted after a normal shutdown.",
                "model": "RE-S-1800x4",
                "up_time": "9 days, 22 hours, 27 minutes, 12 seconds",
                "mastership_state": "master",
            },
        )
        self.assertEqual(
            self.dev.facts["RE1"],
            {
                "status": "OK",
                "last_reboot_reason": "Router rebooted after a normal shutdown.",
                "model": "RE-S-1800x4",
                "up_time": "9 days, 22 hours, 26 minutes, 48 seconds",
                "mastership_state": "backup",
            },
        )
        self.assertEqual(
            self.dev.facts["re_info"],
            {
                "default": {
                    "1": {
                        "status": "OK",
                        "last_reboot_reason": "Router "
                        "rebooted "
                        "after a "
                        "normal "
                        "shutdown.",
                        "model": "RE-S-1800x4",
                        "mastership_state": "backup",
                    },
                    "0": {
                        "status": "OK",
                        "last_reboot_reason": "Router "
                        "rebooted "
                        "after a "
                        "normal "
                        "shutdown.",
                        "model": "RE-S-1800x4",
                        "mastership_state": "master",
                    },
                    "default": {
                        "status": "OK",
                        "last_reboot_reason": "Router rebooted after a "
                        "normal shutdown.",
                        "model": "RE-S-1800x4",
                        "mastership_state": "master",
                    },
                }
            },
        )
        self.assertEqual(self.dev.facts["re_master"], {"default": "0"})

    @patch("jnpr.junos.Device.execute")
    def test_re_info_single(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_single_re
        self.assertEqual(self.dev.facts["2RE"], False)
        self.assertEqual(self.dev.facts["master"], "RE0")
        self.assertEqual(
            self.dev.facts["RE0"],
            {
                "status": "OK",
                "last_reboot_reason": "Router rebooted after a normal shutdown.",
                "model": "RE-VMX",
                "up_time": "29 days, 22 hours, 41 minutes, 35 seconds",
                "mastership_state": "master",
            },
        )
        self.assertEqual(self.dev.facts["RE1"], None)
        self.assertEqual(
            self.dev.facts["re_info"],
            {
                "default": {
                    "default": {
                        "status": "OK",
                        "last_reboot_reason": "Router rebooted "
                        "after a normal "
                        "shutdown.",
                        "model": "RE-VMX",
                        "mastership_state": "master",
                    },
                    "0": {
                        "status": "OK",
                        "last_reboot_reason": "Router rebooted after a "
                        "normal shutdown.",
                        "model": "RE-VMX",
                        "mastership_state": "master",
                    },
                }
            },
        )
        self.assertEqual(self.dev.facts["re_master"], {"default": "0"})

    @patch("jnpr.junos.Device.execute")
    def test_re_info_mx_vc(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_mx_vc
        self.assertEqual(self.dev.facts["2RE"], True)
        self.assertEqual(self.dev.facts["master"], ["RE1", "RE0"])
        self.assertEqual(
            self.dev.facts["RE0"],
            {
                "status": "OK",
                "last_reboot_reason": "Router rebooted after a normal shutdown.",
                "model": "RE-S-1800x4",
                "up_time": "16 days, 13 hours, 17 minutes, 25 seconds",
                "mastership_state": "backup",
            },
        )
        self.assertEqual(
            self.dev.facts["RE1"],
            {
                "status": "OK",
                "last_reboot_reason": "Router rebooted after a normal shutdown.",
                "model": "RE-S-1800x4",
                "up_time": "18 days, 22 hours, 3 minutes, 18 seconds",
                "mastership_state": "master",
            },
        )
        self.assertEqual(
            self.dev.facts["re_info"],
            {
                "default": {
                    "1": {
                        "status": "OK",
                        "last_reboot_reason": "Router "
                        "rebooted "
                        "after a "
                        "normal "
                        "shutdown.",
                        "model": "RE-S-1800x4",
                        "mastership_state": "master",
                    },
                    "0": {
                        "status": "OK",
                        "last_reboot_reason": "Router "
                        "rebooted "
                        "after a "
                        "normal "
                        "shutdown.",
                        "model": "RE-S-1800x4",
                        "mastership_state": "backup",
                    },
                    "default": {
                        "status": "OK",
                        "last_reboot_reason": "Router rebooted after "
                        "a normal shutdown.",
                        "model": "RE-S-1800x4",
                        "mastership_state": "backup",
                    },
                },
                "member1": {
                    "1": {
                        "status": "OK",
                        "last_reboot_reason": "Router "
                        "rebooted "
                        "after a "
                        "normal "
                        "shutdown.",
                        "model": "RE-S-1800x4",
                        "mastership_state": "backup",
                    },
                    "0": {
                        "status": "OK",
                        "last_reboot_reason": "Router "
                        "rebooted "
                        "after a "
                        "normal "
                        "shutdown.",
                        "model": "RE-S-1800x4",
                        "mastership_state": "master",
                    },
                },
                "member0": {
                    "1": {
                        "status": "OK",
                        "last_reboot_reason": "Router "
                        "rebooted "
                        "after a "
                        "normal "
                        "shutdown.",
                        "model": "RE-S-1800x4",
                        "mastership_state": "master",
                    },
                    "0": {
                        "status": "OK",
                        "last_reboot_reason": "Router "
                        "rebooted "
                        "after a "
                        "normal "
                        "shutdown.",
                        "model": "RE-S-1800x4",
                        "mastership_state": "backup",
                    },
                    "default": {
                        "status": "OK",
                        "last_reboot_reason": "Router "
                        "rebooted "
                        "after a "
                        "normal "
                        "shutdown.",
                        "model": "RE-S-1800x4",
                        "mastership_state": "backup",
                    },
                },
            },
        )

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

    def _mock_manager_dual_re(self, *args, **kwargs):
        if args:
            return self._read_file("re_info_dual_" + args[0].tag + ".xml")

    def _mock_manager_single_re(self, *args, **kwargs):
        if args:
            return self._read_file("re_info_single_" + args[0].tag + ".xml")

    def _mock_manager_mx_vc(self, *args, **kwargs):
        if args:
            return self._read_file("re_info_mx_vc_" + args[0].tag + ".xml")
