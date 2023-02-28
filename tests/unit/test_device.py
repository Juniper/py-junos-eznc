try:
    import unittest2 as unittest
except ImportError:
    import unittest
from nose.plugins.attrib import attr
from mock import MagicMock, patch, mock_open, call
import os
from lxml import etree
import sys
import json

from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession
import ncclient.transport.errors as NcErrors
from ncclient.operations import RPCError, TimeoutExpiredError

from jnpr.junos.facts.swver import version_info
from jnpr.junos import Device
from jnpr.junos.exception import RpcError
from jnpr.junos import exception as EzErrors
from jnpr.junos.console import Console

__author__ = "Rick Sherman, Nitin Kumar, Stacy Smith"
__credits__ = "Jeremy Schulman"

if sys.version < "3":
    builtin_string = "__builtin__"
else:
    builtin_string = "builtins"

facts = {
    "domain": None,
    "hostname": "firefly",
    "ifd_style": "CLASSIC",
    "version_info": version_info("15.1X46-D15.3"),
    "2RE": False,
    "serialnumber": "aaf5fe5f9b88",
    "fqdn": "firefly",
    "virtual": True,
    "switch_style": "NONE",
    "version": "12.1X46-D15.3",
    "HOME": "/cf/var/home/rick",
    "srx_cluster": False,
    "model": "FIREFLY-PERIMETER",
    "RE0": {
        "status": "Testing",
        "last_reboot_reason": "Router rebooted after a " "normal shutdown.",
        "model": "FIREFLY-PERIMETER RE",
        "up_time": "6 hours, 29 minutes, 30 seconds",
    },
    "vc_capable": False,
    "personality": "SRX_BRANCH",
}


@attr("unit")
class Test_MyTemplateLoader(unittest.TestCase):
    def setUp(self):
        from jnpr.junos.device import _MyTemplateLoader

        self.template_loader = _MyTemplateLoader()

    @patch(builtin_string + ".filter")
    def test_temp_load_get_source_filter_false(self, filter_mock):
        filter_mock.return_value = []
        try:
            self.template_loader.get_source(None, None)
        except Exception as ex:
            import jinja2

            self.assertEqual(type(ex), jinja2.exceptions.TemplateNotFound)

    @patch("jnpr.junos.device.os.path")
    def test_temp_load_get_source_filter_true(self, os_path_mock):
        # cant use @patch here as with statement will have exit
        m = mock_open()
        with patch(builtin_string + ".open", m, create=True):
            self.template_loader.get_source(None, None)


@attr("unit")
class TestDevice(unittest.TestCase):
    @patch("ncclient.manager.connect")
    def setUp(self, mock_connect):
        mock_connect.side_effect = self._mock_manager

        self.dev = Device(
            host="1.1.1.1", user="test", password="password123", gather_facts=False
        )
        self.dev.open()

    @patch("ncclient.operations.session.CloseSession.request")
    def tearDown(self, mock_session):
        self.dev.close()

    def test_new_console_return(self):
        dev = Device(
            host="1.1.1.1",
            user="test",
            password="password123",
            port=23,
            gather_facts=False,
        )
        self.assertTrue(isinstance(dev, Console))

    @patch("jnpr.junos.device.netconf_ssh")
    def test_device_ConnectAuthError(self, mock_manager):
        mock_manager.connect.side_effect = NcErrors.AuthenticationError
        self.assertRaises(EzErrors.ConnectAuthError, self.dev.open)

    @patch("jnpr.junos.device.netconf_ssh")
    def test_device_ConnectRefusedError(self, mock_manager):
        mock_manager.connect.side_effect = NcErrors.SSHError
        self.assertRaises(EzErrors.ConnectRefusedError, self.dev.open)

    @patch("jnpr.junos.device.netconf_ssh")
    @patch("jnpr.junos.device.datetime")
    def test_device_ConnectTimeoutError(self, mock_datetime, mock_manager):
        mock_manager.connect.side_effect = NcErrors.SSHError(
            "Could not open socket to 1.1.1.1:830"
        )
        from datetime import timedelta, datetime

        currenttime = datetime.now()
        mock_datetime.datetime.now.side_effect = [
            currenttime,
            currenttime + timedelta(minutes=4),
        ]
        self.assertRaises(EzErrors.ConnectTimeoutError, self.dev.open)

    @patch("jnpr.junos.device.netconf_ssh")
    @patch("jnpr.junos.device.datetime")
    def test_device_diff_err_message(self, mock_datetime, mock_manager):
        NcErrors.SSHError.message = "why are you trying :)"
        mock_manager.connect.side_effect = NcErrors.SSHError
        from datetime import timedelta, datetime

        currenttime = datetime.now()
        mock_datetime.datetime.now.side_effect = [
            currenttime,
            currenttime + timedelta(minutes=4),
        ]
        self.assertRaises(EzErrors.ConnectError, self.dev.open)

    @patch("jnpr.junos.device.netconf_ssh")
    def test_device_ConnectUnknownHostError(self, mock_manager):
        import socket

        mock_manager.connect.side_effect = socket.gaierror
        self.assertRaises(EzErrors.ConnectUnknownHostError, self.dev.open)

    @patch("jnpr.junos.device.netconf_ssh")
    def test_device_other_error(self, mock_manager):
        mock_manager.connect.side_effect = TypeError
        self.assertRaises(EzErrors.ConnectError, self.dev.open)

    def test_device_probe_error(self):
        mock_probe = MagicMock()
        mock_probe.return_value = None
        self.dev.probe = mock_probe

        def fn():
            self.dev.open(auto_probe=1)

        self.assertRaises(EzErrors.ProbeError, fn)

    def test_device_property_logfile_isinstance(self):
        mock = MagicMock()
        with patch(builtin_string + ".open", mock):
            if sys.version > "3":
                builtin_file = "io.TextIOWrapper"
            else:
                builtin_file = builtin_string + ".file"
            with patch(builtin_file, MagicMock):
                handle = open("filename", "r")
                self.dev.logfile = handle
                self.assertEqual(self.dev.logfile, handle)

    def test_device_host_mand_param(self):
        self.assertRaises(
            ValueError, Device, user="test", password="password123", gather_facts=False
        )

    def test_device_property_logfile_close(self):
        self.dev._logfile = MagicMock()
        self.dev._logfile.close.return_value = 0
        self.dev.logfile = None
        self.assertFalse(self.dev._logfile)

    def test_device_property_logfile_exception(self):
        try:
            self.dev.logfile = True
        except Exception as ex:
            self.assertEqual(type(ex), ValueError)

    @patch("jnpr.junos.Device.execute")
    def test_device_uptime(self, mock_execute):
        localdev = Device(
            host="1.1.1.1", user="test", password="password123", gather_facts=False
        )
        mock_execute.side_effect = self._mock_manager
        self.assertEqual(localdev.uptime, 14234)

    def test_device_master_is_master(self):
        localdev = Device(
            host="1.1.1.1", user="test", password="password123", gather_facts=False
        )
        localdev.facts._cache["current_re"] = [
            "re1",
            "master",
            "node",
            "fwdd",
            "member",
            "pfem",
        ]
        self.assertEqual(localdev.master, True)

    def test_device_master_gnf_is_master(self):
        localdev = Device(
            host="1.1.1.1", user="test", password="password123", gather_facts=False
        )
        localdev.facts._cache["current_re"] = ["gnf1-re0", "gnf1-master"]
        localdev.facts._cache["hostname_info"] = {
            "bsys-re0": "foo",
            "bsys-re1": "foo1",
            "gnf1-re0": "bar",
            "gnf1-re1": "bar1",
        }
        self.assertEqual(localdev.master, True)

    def test_device_master_is_backup(self):
        localdev = Device(
            host="1.1.1.1", user="test", password="password123", gather_facts=False
        )
        localdev.facts._cache["current_re"] = ["re0", "backup"]
        self.assertEqual(localdev.master, False)

    def test_device_master_gnf_is_backup(self):
        localdev = Device(
            host="1.1.1.1", user="test", password="password123", gather_facts=False
        )
        localdev.facts._cache["current_re"] = ["gnf1-re1", "gnf1-backup"]
        localdev.facts._cache["hostname_info"] = {
            "bsys-re0": "foo",
            "bsys-re1": "foo1",
            "gnf1-re0": "bar",
            "gnf1-re1": "bar1",
        }
        self.assertEqual(localdev.master, False)

    def test_device_master_is_re0_only(self):
        localdev = Device(
            host="1.1.1.1", user="test", password="password123", gather_facts=False
        )
        localdev.facts._cache["2RE"] = False
        localdev.facts._cache["RE_hw_mi"] = False
        localdev.facts._cache["current_re"] = ["re0"]
        self.assertEqual(localdev.master, True)

    def test_device_master_is_multi_chassis_non_master1(self):
        localdev = Device(
            host="1.1.1.1", user="test", password="password123", gather_facts=False
        )
        localdev.facts._cache["2RE"] = True
        localdev.facts._cache["current_re"] = [
            "lcc1-re1",
            "member1-re1",
            "lcc1-backup",
            "member1-backup",
        ]
        self.assertEqual(localdev.master, False)

    def test_device_master_is_multi_chassis_non_master2(self):
        localdev = Device(
            host="1.1.1.1", user="test", password="password123", gather_facts=False
        )
        localdev.facts._cache["2RE"] = True
        localdev.facts._cache["current_re"] = [
            "lcc1-re0",
            "member1-re0",
            "lcc1-master",
            "member1-master",
            "member1",
        ]
        self.assertEqual(localdev.master, False)

    def test_device_master_is_none1(self):
        localdev = Device(
            host="1.1.1.1", user="test", password="password123", gather_facts=False
        )
        localdev.facts._cache["current_re"] = None
        self.assertEqual(localdev.master, None)

    def test_device_master_is_none2(self):
        localdev = Device(
            host="1.1.1.1", user="test", password="password123", gather_facts=False
        )
        localdev.facts._cache["2RE"] = True
        localdev.facts._cache["current_re"] = ["foo", "bar"]
        self.assertEqual(localdev.master, None)

    @patch("jnpr.junos.device.warnings")
    def test_device_master_is_old_facts(self, mock_warn):
        localdev = Device(
            host="1.1.1.1",
            user="test",
            password="password123",
            fact_style="old",
            gather_facts=False,
        )
        mock_warn.assert_has_calls(
            [
                call.warn(
                    "fact-style old will be removed " "in a future release.",
                    RuntimeWarning,
                )
            ]
        )
        self.assertEqual(localdev.master, None)

    def test_device_master_setter(self):
        localdev = Device(
            host="1.1.1.1", user="test", password="password123", gather_facts=False
        )
        with self.assertRaises(RuntimeError):
            localdev.master = "foo"

    def test_device_re_name_is_re0(self):
        localdev = Device(
            host="1.1.1.1", user="test", password="password123", gather_facts=False
        )
        localdev.facts._cache["current_re"] = ["re0", "backup"]
        localdev.facts._cache["hostname_info"] = {"re0": "tapir", "re1": "tapir1"}
        self.assertEqual(localdev.re_name, "re0")

    def test_device_re_name_is_lcc_re1(self):
        localdev = Device(
            host="1.1.1.1", user="test", password="password123", gather_facts=False
        )
        localdev.facts._cache["current_re"] = [
            "lcc1-re1",
            "member1-re1",
            "lcc1-backup",
            "member1-backup",
        ]
        localdev.facts._cache["hostname_info"] = {"re0": "mj1"}
        self.assertEqual(localdev.re_name, "lcc1-re1")

    def test_device_re_name_is_re0_only(self):
        localdev = Device(
            host="1.1.1.1", user="test", password="password123", gather_facts=False
        )
        localdev.facts._cache["current_re"] = ["foo"]
        localdev.facts._cache["hostname_info"] = {"re0": "mj1"}
        self.assertEqual(localdev.re_name, "re0")

    def test_device_re_name_is_bsys_re0(self):
        localdev = Device(
            host="1.1.1.1", user="test", password="password123", gather_facts=False
        )
        localdev.facts._cache["current_re"] = ["re0"]
        localdev.facts._cache["hostname_info"] = {"bsys-re0": "foo"}
        self.assertEqual(localdev.re_name, "bsys-re0")

    def test_device_re_name_is_none1(self):
        localdev = Device(
            host="1.1.1.1", user="test", password="password123", gather_facts=False
        )
        localdev.facts._cache["current_re"] = None
        self.assertEqual(localdev.re_name, None)

    def test_device_re_name_is_none2(self):
        localdev = Device(
            host="1.1.1.1", user="test", password="password123", gather_facts=False
        )
        localdev.facts._cache["current_re"] = [
            "re1",
            "master",
            "node",
            "fwdd",
            "member",
            "pfem",
        ]
        localdev.facts._cache["hostname_info"] = None
        self.assertEqual(localdev.re_name, None)

    @patch("jnpr.junos.device.warnings")
    def test_device_re_name_is_old_facts(self, mock_warn):
        localdev = Device(
            host="1.1.1.1",
            user="test",
            password="password123",
            fact_style="old",
            gather_facts=False,
        )
        mock_warn.assert_has_calls(
            [
                call.warn(
                    "fact-style old will be removed " "in a future release.",
                    RuntimeWarning,
                )
            ]
        )
        self.assertEqual(localdev.re_name, None)

    def test_device_re_name_setter(self):
        localdev = Device(
            host="1.1.1.1", user="test", password="password123", gather_facts=False
        )
        with self.assertRaises(RuntimeError):
            localdev.re_name = "foo"

    def test_device_repr(self):
        localdev = Device(
            host="1.1.1.1", user="test", password="password123", gather_facts=False
        )
        self.assertEqual(repr(localdev), "Device(1.1.1.1)")

    def test_device_local(self):
        Device.ON_JUNOS = True
        localdev = Device()
        self.assertEqual(localdev._hostname, "localhost")

    @patch("jnpr.junos.device.os")
    @patch(builtin_string + ".open")
    @patch("paramiko.config.SSHConfig.lookup")
    def test_device__sshconf_lkup(self, mock_paramiko, open_mock, os_mock):
        os_mock.path.exists.return_value = True
        self.dev._sshconf_lkup()
        mock_paramiko.assert_called_once_with("1.1.1.1")

    @patch("jnpr.junos.device.os")
    @patch(builtin_string + ".open")
    @patch("paramiko.config.SSHConfig.lookup")
    def test_device__sshconf_lkup_def(self, mock_paramiko, open_mock, os_mock):
        os_mock.path.exists.return_value = True
        self.dev._ssh_config = "/home/rsherman/.ssh/config"
        self.dev._sshconf_lkup()
        mock_paramiko.assert_called_once_with("1.1.1.1")

    @patch("paramiko.config.SSHConfig.lookup")
    def test_device__sshconf_lkup_sock_fd(self, mock_paramiko):
        self.dev2 = Device(sock_fd=6)
        self.dev2._sshconf_lkup()
        self.assertEqual(self.dev2._sshconf_lkup(), None)

    @patch("os.path.expanduser")
    def test_device__sshconf_lkup_path_not_exists(self, mock_path):
        mock_path.return_value = "/home/test"
        self.assertEqual(self.dev._sshconf_lkup(), None)

    @patch("ncclient.manager.connect")
    @patch("jnpr.junos.Device.execute")
    def test_device_open(self, mock_connect, mock_execute):
        with patch("jnpr.junos.utils.fs.FS.cat") as mock_cat:
            mock_cat.return_value = """

    domain jls.net

            """
            mock_connect.side_effect = self._mock_manager
            mock_execute.side_effect = self._mock_manager
            self.dev2 = Device(host="2.2.2.2", user="test", password="password123")
            self.dev2.open()
            self.assertEqual(self.dev2.connected, True)

    @patch("ncclient.manager.connect")
    @patch("jnpr.junos.Device.execute")
    def test_device_open_with_look_for_keys_False(self, mock_connect, mock_execute):
        with patch("jnpr.junos.utils.fs.FS.cat") as mock_cat:
            mock_cat.return_value = """

    domain jls.net

            """
            mock_connect.side_effect = self._mock_manager
            mock_execute.side_effect = self._mock_manager
            self.dev2 = Device(host="2.2.2.2", user="test", password="password123", look_for_keys=False)
            self.dev2.open()
            self.assertEqual(self.dev2.connected, True)

    @patch("ncclient.manager.connect")
    @patch("jnpr.junos.Device.execute")
    def test_device_open_with_look_for_keys_True(self, mock_connect, mock_execute):
        with patch("jnpr.junos.utils.fs.FS.cat") as mock_cat:
            mock_cat.return_value = """

    domain jls.net

            """
            mock_connect.side_effect = self._mock_manager
            mock_execute.side_effect = self._mock_manager
            self.dev2 = Device(host="2.2.2.2", user="test", password="password123", look_for_keys=True)
            self.dev2.open()
            self.assertEqual(self.dev2.connected, True)

    @patch("ncclient.manager.connect")
    @patch("jnpr.junos.Device.execute")
    def test_device_outbound(self, mock_connect, mock_execute):
        with patch("jnpr.junos.utils.fs.FS.cat") as mock_cat:
            mock_cat.return_value = """

    domain jls.net

            """
            mock_connect.side_effect = self._mock_manager
            mock_execute.side_effect = self._mock_manager
            self.dev2 = Device(sock_fd=6, user="test", password="password123")
            self.dev2.open()
            self.assertEqual(self.dev2.connected, True)

    @patch("jnpr.junos.Device.execute")
    def test_device_facts(self, mock_execute):
        with patch("jnpr.junos.utils.fs.FS.cat") as mock_cat:
            mock_execute.side_effect = self._mock_manager
            mock_cat.return_value = """

    domain jls.net

            """
            self.dev.facts_refresh()
            self.dev.facts._cache["current_re"] = ["re0"]
            assert self.dev.facts["version"] == facts["version"]

    @patch("jnpr.junos.Device.execute")
    @patch("jnpr.junos.factcache.warnings")
    def test_device_facts_error(self, mock_warnings, mock_execute):
        with patch("jnpr.junos.utils.fs.FS.cat") as mock_cat:
            mock_execute.side_effect = self._mock_manager
            mock_cat.side_effect = IOError("File cant be handled")
            self.dev.facts_refresh(warnings_on_failure=True)
            self.assertTrue(mock_warnings.warn.called)

    @patch("jnpr.junos.Device.execute")
    @patch("jnpr.junos.device.warnings")
    def test_device_facts_error_exception_on_error(self, mock_warnings, mock_execute):
        with patch("jnpr.junos.utils.fs.FS.cat") as mock_cat:
            mock_execute.side_effect = self._mock_manager
            mock_cat.side_effect = IOError("File cant be handled")
            self.assertRaises(
                IOError, self.dev.facts_refresh, exception_on_failure=True
            )

    @patch("jnpr.junos.Device.execute")
    @patch("jnpr.junos.device.warnings")
    def test_device_old_style_facts_error_exception_on_error(
        self, mock_warnings, mock_execute
    ):
        self.dev._fact_style = "old"
        with patch("jnpr.junos.utils.fs.FS.cat") as mock_cat:
            mock_execute.side_effect = self._mock_manager
            mock_cat.side_effect = IOError("File cant be handled")
            self.assertRaises(
                IOError, self.dev.facts_refresh, exception_on_failure=True
            )

    def test_device_facts_refresh_unknown_fact_style(self):
        self.dev._fact_style = "bad"
        with self.assertRaises(RuntimeError):
            self.dev.facts_refresh()

    def test_device_facts_refresh_old_fact_style_with_keys(self):
        self.dev._fact_style = "old"
        with self.assertRaises(RuntimeError):
            self.dev.facts_refresh(keys="domain")

    def test_device_hostname(self):
        self.assertEqual(self.dev.hostname, "1.1.1.1")

    def test_device_user(self):
        self.assertEqual(self.dev.user, "test")

    def test_device_get_password(self):
        self.assertEqual(self.dev.password, None)

    def test_device_set_password(self):
        self.dev.password = "secret"
        self.assertEqual(self.dev._auth_password, "secret")

    def test_device_get_timeout(self):
        self.assertEqual(self.dev.timeout, 30)

    def test_device_set_timeout(self):
        self.dev.timeout = 10
        self.assertEqual(self.dev.timeout, 10)

    def test_device_set_timeout_string(self):
        self.dev.timeout = "10"
        self.assertEqual(self.dev.timeout, 10)

    def test_device_set_timeout_invalid_string_value(self):
        with self.assertRaises(RuntimeError):
            self.dev.timeout = "foo"

    def test_device_set_timeout_invalid_type(self):
        with self.assertRaises(RuntimeError):
            self.dev.timeout = [1, 2, 3, 4]

    def test_device_manages(self):
        self.assertEqual(self.dev.manages, [], "By default manages will be empty list")

    @patch("ncclient.manager.connect")
    @patch("jnpr.junos.Device.execute")
    def test_device_open_normalize(self, mock_connect, mock_execute):
        mock_connect.side_effect = self._mock_manager
        self.dev2 = Device(host="2.2.2.2", user="test", password="password123")
        self.dev2.open(gather_facts=False, normalize=True)
        self.assertEqual(self.dev2.transform, self.dev2._norm_transform)

    def test_device_conn_None_transform(self):
        self.dev = Device(host="2.2.2.2", user="test", password="password123")
        with self.assertRaises(EzErrors.ConnectError):
            self.dev.transform

    def test_device_set_facts_exception(self):
        try:
            self.dev.facts = "test"
        except RuntimeError as ex:
            self.assertEqual(RuntimeError, type(ex))

    def test_device_ofacts_exception(self):
        with self.assertRaises(RuntimeError):
            ofacts = self.dev.ofacts

    def test_device_set_ofacts_exception(self):
        with self.assertRaises(RuntimeError):
            self.dev.ofacts = False

    @patch("jnpr.junos.Device.execute")
    def test_device_cli(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.assertEqual(self.dev.cli("show cli directory", warning=False).tag, "cli")

    @patch("jnpr.junos.device.json.loads")
    def test_device_rpc_json_ex(self, mock_json_loads):
        self.dev.facts = facts
        self.dev._conn.rpc = MagicMock(side_effect=self._mock_manager)
        ex = ValueError("Extra data ")
        ex.message = "Extra data "  # for py3 as we dont have message thr
        mock_json_loads.side_effect = [
            ex,
            self._mock_manager(
                etree.fromstring('<get-route-information format="json"/>')
            ),
        ]
        self.dev.rpc.get_route_information({"format": "json"})
        self.assertEqual(mock_json_loads.call_count, 2)

    @patch("jnpr.junos.Device.execute")
    def test_device_cli_to_rpc_string(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        data = self.dev.cli_to_rpc_string("show system uptime")
        self.assertEqual("rpc.get_system_uptime_information()", data)

    @patch("jnpr.junos.Device.execute")
    def test_device_cli_to_rpc_string_strip_pipes(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        data = self.dev.cli_to_rpc_string("show system uptime | match foo | count")
        self.assertEqual("rpc.get_system_uptime_information()", data)

    @patch("jnpr.junos.Device.execute")
    def test_device_cli_to_rpc_string_complex(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        data = self.dev.cli_to_rpc_string(
            "show interfaces ge-0/0/0.0 routing-instance all media"
        )
        self.assertEqual(
            "rpc.get_interface_information("
            "routing_instance='all', media=True, "
            "interface_name='ge-0/0/0.0')",
            data,
        )

    @patch("jnpr.junos.Device.execute")
    def test_device_cli_to_rpc_string_invalid(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        data = self.dev.cli_to_rpc_string("foo")
        self.assertEqual(None, data)

    @patch("jnpr.junos.Device.execute")
    def test_device_cli_format_json(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        data = self.dev.cli("show interface terse", warning=False, format="json")
        self.assertEqual(type(data), dict)
        self.assertEqual(
            data["interface-information"][0]["physical-interface"][0]["oper-status"][0][
                "data"
            ],
            "up",
        )

    @patch("jnpr.junos.Device.execute")
    def test_device_cli_conf_info(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.assertTrue("ge-0/0/0" in self.dev.cli("show configuration", warning=False))

    @patch("jnpr.junos.Device.execute")
    def test_device_cli_output(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.assertTrue("Alarm" in self.dev.cli("show system alarms", warning=False))

    @patch("jnpr.junos.Device.execute")
    @patch("jnpr.junos.device.warnings")
    def test_device_cli_output_warning(self, mock_warnings, mock_execute):
        mock_execute.side_effect = self._mock_manager
        data = self.dev.cli(
            "show interfaces ge-0/0/0.0 routing-instance " "all media", format="xml"
        )
        ip = data.findtext(
            'logical-interface[name="ge-0/0/0.0"]/'
            'address-family[address-family-name="inet"]/'
            "interface-address/ifa-local"
        )
        self.assertTrue("192.168.100.1" in ip)
        self.assertTrue(mock_warnings.warn.called)
        rpc_string = (
            "rpc.get_interface_information(routing_instance='all', "
            "media=True, interface_name='ge-0/0/0.0')"
        )
        self.assertIn(rpc_string, mock_warnings.warn.call_args[0][0])

    def test_device_cli_blank_output(self):
        self.dev._conn.rpc = MagicMock(side_effect=self._mock_manager)
        self.assertEqual(
            "", self.dev.cli("show configuration interfaces", warning=False)
        )

    def test_device_cli_rpc_reply_with_message(self):
        self.dev._conn.rpc = MagicMock(side_effect=self._mock_manager)
        self.assertEqual(
            "\nprotocol: operation-failed\nerror: device asdf not found\n",
            self.dev.cli("show interfaces terse asdf", warning=False),
        )

    @patch("jnpr.junos.Device.execute")
    def test_device_cli_rpc(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.assertEqual(
            self.dev.cli("show system uptime| display xml rpc", warning=False).tag,
            "get-system-uptime-information",
        )

    def test_device_cli_connection_exception(self):
        self.dev.connected = False
        self.assertRaises(EzErrors.ConnectClosedError, self.dev.cli, "foo")

    @patch("jnpr.junos.Device.execute")
    def test_device_cli_rpc_exception(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.assertRaises(EzErrors.RpcError, self.dev.cli, "foo")

    def test_device_cli_timeout_exception(self):
        self.dev._conn.rpc = MagicMock(side_effect=TimeoutExpiredError)
        self.assertRaises(EzErrors.RpcTimeoutError, self.dev.cli, "foo")

    @patch("jnpr.junos.device.warnings")
    def test_device_cli_unknown_exception(self, mock_warnings):
        class MyException(Exception):
            pass

        self.dev._conn.rpc = MagicMock(side_effect=MyException)
        self.assertRaises(MyException, self.dev.cli, "foo")

    @patch("jnpr.junos.Device.execute")
    def test_device_display_xml_rpc(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.assertEqual(
            self.dev.display_xml_rpc("show system uptime").tag,
            "get-system-uptime-information",
        )

    @patch("jnpr.junos.Device.execute")
    def test_device_display_xml_rpc_text(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.assertIn(
            "<get-system-uptime-information>",
            self.dev.display_xml_rpc("show system uptime", format="text"),
        )

    @patch("jnpr.junos.Device.execute")
    def test_device_display_xml_exception(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.assertEqual(
            self.dev.display_xml_rpc("show foo"),
            "invalid command: show foo| display xml rpc",
        )

    def test_device_execute(self):
        self.dev._conn.rpc = MagicMock(side_effect=self._mock_manager)
        self.assertEqual(
            self.dev.execute("<get-system-core-dumps/>").tag, "directory-list"
        )

    def test_device_execute_topy(self):
        self.dev._conn.rpc = MagicMock(side_effect=self._mock_manager)
        self.assertEqual(
            self.dev.execute("<get-system-core-dumps/>", to_py=self._do_nothing),
            "Nothing",
        )

    # This test is for the commented out rpc-error code
    #     def test_device_execute_exception(self):
    #         self.dev._conn.rpc = MagicMock(side_effect=self._mock_manager)
    #         self.assertRaises(RpcError, self.dev.execute,
    #                           '<load-configuration-error/>')

    @patch("jnpr.junos.device.warnings")
    def test_device_execute_unknown_exception(self, mock_warnings):
        class MyException(Exception):
            pass

        self.dev._conn.rpc = MagicMock(side_effect=MyException)
        self.assertRaises(MyException, self.dev.execute, "<get-software-information/>")

    def test_device_execute_rpc_error(self):
        self.dev._conn.rpc = MagicMock(side_effect=self._mock_manager)
        self.assertRaises(RpcError, self.dev.rpc.get_rpc_error)

    @unittest.skipIf(sys.platform == "win32", "will work for windows in coming days")
    def test_device_execute_permission_error(self):
        self.dev._conn.rpc = MagicMock(side_effect=self._mock_manager)
        self.assertRaises(EzErrors.PermissionError, self.dev.rpc.get_permission_denied)

    def test_device_execute_index_error(self):
        self.dev._conn.rpc = MagicMock(side_effect=self._mock_manager)
        self.assertTrue(self.dev.rpc.get_index_error())

    def test_device_execute_ValueError(self):
        self.assertRaises(ValueError, self.dev.execute, None)

    def test_device_execute_unopened(self):
        self.dev.connected = False
        self.assertRaises(EzErrors.ConnectClosedError, self.dev.execute, None)

    def test_device_execute_timeout(self):
        self.dev._conn.rpc = MagicMock(side_effect=TimeoutExpiredError)
        self.assertRaises(EzErrors.RpcTimeoutError, self.dev.rpc.get_rpc_timeout)

    def test_device_execute_closed(self):
        self.dev._conn.rpc = MagicMock(side_effect=NcErrors.TransportError)
        self.assertRaises(EzErrors.ConnectClosedError, self.dev.rpc.get_rpc_close)
        self.assertFalse(self.dev.connected)

    def test_device_rpcmeta(self):
        self.assertEqual(
            self.dev.rpc.get_software_information.__doc__, "get-software-information"
        )

    def test_device_probe_timeout_zero(self):
        with patch("jnpr.junos.device.socket"):
            self.assertFalse(self.dev.probe(0))

    def test_device_probe_timeout_gt_zero(self):
        with patch("jnpr.junos.device.socket"):
            self.assertTrue(
                self.dev.probe(1),
                "probe fn is not working for" " timeout greater than zero",
            )

    def test_device_probe_timeout_exception(self):
        with patch("jnpr.junos.device.socket") as mock_socket:
            with patch("jnpr.junos.device.time.sleep") as mock_time:
                mock_socket.socket.return_value.close.side_effect = RuntimeError
                mock_time.return_value = None
                self.assertFalse(self.dev.probe(0.01))

    def test_device_bind_varg(self):
        self.dev.bind()
        mock = MagicMock()
        mock.__name__ = "magic_mock"
        self.dev.bind(mock)
        self.assertEqual(self.dev.magic_mock.__name__, "magic_mock")

    def test_device_bind_kvarg(self):
        self.dev.bind()
        mock = MagicMock()
        mock.return_value = "Test"
        self.dev.bind(kw=mock)
        self.assertEqual(self.dev.kw, "Test")

    def test_device_bind_varg_exception(self):
        def varg():
            self.dev.bind()
            mock = MagicMock()
            mock.__name__ = "magic mock"
            # for *args
            self.dev.bind(mock)
            self.dev.bind(mock)

        self.assertRaises(ValueError, varg)

    def test_device_bind_kvarg_exception(self):
        def kve():
            self.dev.bind()
            mock = MagicMock()
            mock.__name__ = "magic mock"
            # for **kwargs
            self.dev.bind(kw=mock)
            self.dev.bind(kw=mock)

        self.assertRaises(ValueError, kve)

    def test_device_template(self):
        # Try to load the template relative to module base
        try:
            template = self.dev.Template("tests/unit/templates/config-example.xml")
        except:
            # Try to load the template relative to test base
            try:
                template = self.dev.Template("templates/config-example.xml")
            except:
                raise
        self.assertEqual(
            template.render({"host_name": "1", "domain_name": "2"}),
            "system {\n  host-name 1;\n  domain-name 2;\n}",
        )

    def test_device_close(self):
        def close_conn():
            self.dev.connected = False

        self.dev.close = MagicMock(name="close")
        self.dev.close.side_effect = close_conn
        self.dev.close()
        self.assertEqual(self.dev.connected, False)

    @patch("ncclient.manager.connect")
    def test_device_context_manager(self, mock_connect):
        mock_connect.side_effect = self._mock_manager
        try:
            with Device(
                host="3.3.3.3", user="gic", password="password123", gather_facts=False
            ) as dev:
                self.assertTrue(dev.connected)
                dev._conn = MagicMock(name="_conn")
                dev._conn.connected = True

                def close_conn():
                    dev.connected = False

                dev.close = MagicMock(name="close")
                dev.close.side_effect = close_conn
                raise RpcError
        except Exception as e:
            self.assertIsInstance(e, RpcError)
        self.assertFalse(dev.connected)

    def _read_file(self, fname):
        from ncclient.xml_ import NCElement

        fpath = os.path.join(os.path.dirname(__file__), "rpc-reply", fname)
        with open(fpath) as fp:
            foo = fp.read()

            if fname == "get-rpc-error.xml":
                # Raise ncclient exception for error
                raise RPCError(etree.XML(foo))
            elif fname == "get-permission-denied.xml":
                # Raise ncclient exception for error
                raise RPCError(etree.XML(foo))
            elif (
                fname == "get-index-error.xml"
                or fname == "get-system-core-dumps.xml"
                or fname == "load-configuration-error.xml"
                or fname == "show-configuration-interfaces.xml"
                or fname == "show-interfaces-terse-asdf.xml"
            ):
                rpc_reply = NCElement(
                    foo, self.dev._conn._device_handler.transform_reply()
                )
            elif fname == "show-configuration.xml" or fname == "show-system-alarms.xml":
                rpc_reply = NCElement(
                    foo, self.dev._conn._device_handler.transform_reply()
                )._NCElement__doc
            elif fname == "show-interface-terse.json":
                rpc_reply = json.loads(foo)
            elif fname == "get-route-information.json":
                rpc_reply = NCElement(
                    foo, self.dev._conn._device_handler.transform_reply()
                )
            else:
                rpc_reply = NCElement(
                    foo, self.dev._conn._device_handler.transform_reply()
                )._NCElement__doc[0]
        return rpc_reply

    def _mock_manager(self, *args, **kwargs):
        if kwargs and "normalize" not in kwargs:
            device_params = kwargs["device_params"]
            device_handler = make_device_handler(device_params)
            session = SSHSession(device_handler)
            return Manager(session, device_handler)
        elif args:
            if args[0].tag == "command":
                if args[0].text == "show cli directory":
                    return self._read_file("show-cli-directory.xml")
                if args[0].text == "show interface terse":
                    return self._read_file("show-interface-terse.json")
                elif args[0].text == "show configuration":
                    return self._read_file("show-configuration.xml")
                elif args[0].text == "show system alarms":
                    return self._read_file("show-system-alarms.xml")
                elif args[0].text == "show system uptime| display xml rpc":
                    return self._read_file("show-system-uptime-rpc.xml")
                elif args[0].text == "show configuration interfaces":
                    return self._read_file("show-configuration-interfaces.xml")
                elif args[0].text == "show interfaces terse asdf":
                    return self._read_file("show-interfaces-terse-asdf.xml")
                elif (
                    args[0].text == "show interfaces ge-0/0/0.0 "
                    "routing-instance all media"
                ):
                    return self._read_file("show-interfaces-routing-instance-media.xml")
                elif (
                    args[0].text == "show interfaces ge-0/0/0.0 "
                    "routing-instance all media| display "
                    "xml rpc"
                ):
                    return self._read_file(
                        "show-interfaces-routing-instance-media-rpc.xml"
                    )
                else:
                    raise RpcError

            else:
                if args[0].attrib.get("format") == "json":
                    return self._read_file(args[0].tag + ".json")
                return self._read_file(args[0].tag + ".xml")

    def _do_nothing(self, *args, **kwargs):
        return "Nothing"
