try:
    import unittest2 as unittest
except ImportError:
    import unittest
from jnpr.junos.utils.config import Config
import nose2
from mock import patch, MagicMock, call
import re
import sys
import os
from lxml import etree
import six
import socket

from jnpr.junos.console import Console
from jnpr.junos.transport.tty_netconf import tty_netconf
from jnpr.junos.transport.tty_telnet import Terminal


if sys.version < "3":
    builtin_string = "__builtin__"
else:
    builtin_string = "builtins"


class TestConsole(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Save object state
        cls.open = tty_netconf.open

    @classmethod
    def tearDownClass(cls):
        # Revert object state
        tty_netconf.open = cls.open

    @patch("jnpr.junos.transport.tty_telnet.Telnet._tty_open")
    @patch("jnpr.junos.transport.tty_telnet.telnetlib.Telnet.expect")
    @patch("jnpr.junos.transport.tty_telnet.Telnet.write")
    def setUp(self, mock_write, mock_expect, mock_open):
        tty_netconf.open = MagicMock()
        mock_expect.side_effect = [
            (1, re.search("(?P<login>ogin:\s*$)", "login: "), six.b("\r\r\n ogin:")),
            (
                2,
                re.search("(?P<passwd>assword:\s*$)", "password: "),
                six.b("\r\r\n password:"),
            ),
            (
                3,
                re.search("(?P<shell>%|#\s*$)", "junos % "),
                six.b("\r\r\nroot@device:~ # "),
            ),
        ]
        self.dev = Console(host="1.1.1.1", user="lab", password="lab123", mode="Telnet")
        self.dev.open()

    @patch("jnpr.junos.console.Console._tty_logout")
    def tearDown(self, mock_tty_logout):
        self.dev.close()

    def test_telnet_host_none(self):
        self.dev = Console(host=None, user="lab", password="lab123", mode="Telnet")
        self.assertTrue(self.dev.open()["failed"])

    @patch("jnpr.junos.console.warnings")
    def test_telnet_old_fact_warning(self, mock_warn):
        self.dev = Console(
            host="1.1.1.1",
            user="lab",
            password="lab123",
            mode="Telnet",
            fact_style="old",
        )
        mock_warn.assert_has_calls(
            [
                call.warn(
                    "fact-style old will be removed in a future release.",
                    RuntimeWarning,
                )
            ]
        )

    @patch("jnpr.junos.transport.tty_telnet.Telnet._tty_open")
    @patch("jnpr.junos.transport.tty_telnet.telnetlib.Telnet.expect")
    @patch("jnpr.junos.transport.tty_telnet.Telnet.write")
    def test_login_bad_password(self, mock_write, mock_expect, mock_open):
        tty_netconf.open = MagicMock()
        mock_expect.side_effect = [
            (1, re.search("(?P<login>ogin:\s*$)", "login: "), six.b("\r\r\n ogin:")),
            (
                2,
                re.search("(?P<passwd>assword:\s*$)", "password: "),
                six.b("\r\r\n password:"),
            ),
            (
                3,
                re.search("(?P<badpasswd>ogin incorrect)", "login incorrect"),
                six.b("\r\r\nlogin incorrect"),
            ),
        ]
        self.dev = Console(host="1.1.1.1", user="lab", password="lab123", mode="Telnet")
        self.assertRaises(StopIteration, self.dev.open)

    @patch("jnpr.junos.console.Console._tty_logout")
    @patch("jnpr.junos.transport.tty_telnet.Telnet._tty_open")
    @patch("jnpr.junos.transport.tty_telnet.telnetlib.Telnet.expect")
    @patch("jnpr.junos.transport.tty_telnet.Telnet.write")
    def test_with_context(self, mock_write, mock_expect, mock_open, mock_logout):
        tty_netconf.open = MagicMock()

        mock_expect.side_effect = [
            (1, re.search("(?P<login>ogin:\s*$)", "login: "), six.b("\r\r\n ogin:")),
            (
                2,
                re.search("(?P<passwd>assword:\s*$)", "password: "),
                six.b("\r\r\n password:"),
            ),
            (
                3,
                re.search("(?P<shell>%|#\s*$)", "junos % "),
                six.b("\r\r\nroot@device:~ # "),
            ),
        ]
        with Console(
            host="1.1.1.1", user="lab", password="lab123", mode="Telnet"
        ) as dev:
            self.assertTrue(isinstance(self.dev, Console))

    @patch("jnpr.junos.console.Console._tty_login")
    def test_console_open_error(self, mock_tty_login):
        mock_tty_login.side_effect = RuntimeError
        self.assertRaises(RuntimeError, self.dev.open)

    def test_console_connected(self):
        self.assertTrue(self.dev.connected)
        self.assertFalse(self.dev._gather_facts)

    @patch("jnpr.junos.console.Console._tty_logout")
    def test_console_close_error(self, mock_logout):
        mock_logout.side_effect = RuntimeError
        self.assertRaises(RuntimeError, self.dev.close)

    @patch("jnpr.junos.console.Console._tty_logout")
    def test_console_close_socket_error(self, mock_logout):
        mock_logout.side_effect = socket.error
        self.assertRaises(socket.error, self.dev.close)

    @patch("jnpr.junos.console.Console._tty_logout")
    def test_console_close_socket_conn_reset(self, mock_logout):
        mock_logout.side_effect = socket.error("Connection reset by peer")
        self.dev.close()
        self.assertFalse(self.dev.connected)

    @patch("jnpr.junos.console.Console._tty_logout")
    def test_console_close_telnet_conn_closed(self, mock_logout):
        mock_logout.side_effect = EOFError("telnet connection closed")
        self.dev.close()
        self.assertFalse(self.dev.connected)

    @patch("jnpr.junos.transport.tty_telnet.Telnet")
    @patch("jnpr.junos.console.Console._tty_login")
    def test_console_tty_open_err(self, mock_login, mock_telnet):
        with patch(
            "jnpr.junos.transport.tty_telnet." "telnetlib.Telnet.open"
        ) as mock_open:
            mock_telnet.RETRY_OPEN = 1
            mock_login.side_effect = ValueError
            self.dev._tty.LOGIN_RETRY = self.dev._tty.RETRY_OPEN = 1
            self.assertRaises(ValueError, self.dev.open)

    @patch("jnpr.junos.transport.tty_serial.Serial._tty_open")
    @patch("jnpr.junos.transport.tty_serial.serial.Serial.readline")
    @patch("jnpr.junos.transport.tty_serial.Serial.write")
    def test_console_serial(self, mock_write, mock_expect, mock_open):
        tty_netconf.open = MagicMock()
        mock_expect.side_effect = [
            six.b("\r\r\n Login:"),
            six.b("\r\r\n password:"),
            six.b("\r\r\nroot@device:~ # "),
        ]
        self.dev = Console(host="1.1.1.1", user="lab", password="lab123", mode="serial")
        self.dev.open()
        self.assertTrue(self.dev.connected)
        self.assertFalse(self.dev._gather_facts)

    def test_wrong_mode(self):
        dev = Console(host="1.1.1.1", user="lab", password="lab123", mode="testing")
        self.assertRaises(AttributeError, dev.open)

    @patch("jnpr.junos.transport.tty_telnet.Telnet._tty_close")
    def test_console_close_error_skip_logout(self, mock_close):
        mock_close.side_effect = RuntimeError
        self.assertRaises(RuntimeError, self.dev.close, skip_logout=True)

    @patch("jnpr.junos.transport.tty_netconf.tty_netconf.rpc")
    def test_console_zeroize(self, mock_zeroize):
        self.dev.zeroize()
        self.assertTrue(mock_zeroize.called)

    @patch("jnpr.junos.transport.tty_netconf.tty_netconf.rpc")
    @patch("jnpr.junos.console.FACT_LIST")
    @patch("jnpr.junos.device.warnings")
    def test_console_gather_facts(self, mock_warnings, mock_fact_list, mock_rpc):
        self.dev._fact_style = "old"
        from jnpr.junos.ofacts.session import facts_session

        mock_fact_list.__iter__.return_value = [facts_session]
        self.dev.facts_refresh()
        self.assertEqual(mock_rpc.call_count, 8)

    @patch("jnpr.junos.console.Console._tty_login")
    @patch("jnpr.junos.console.FACT_LIST")
    @patch("jnpr.junos.device.warnings")
    def test_console_gather_facts_true(self, mock_warnings, mock_fact_list, tty_login):
        self.dev._fact_style = "old"
        self.dev.facts = self.dev.ofacts
        from jnpr.junos.ofacts.session import facts_session

        mock_fact_list.__iter__.return_value = [facts_session]
        self.dev._gather_facts = True
        self.dev.open()
        self.assertEqual(
            self.dev.facts,
            {
                "2RE": False,
                "RE_hw_mi": False,
                "ifd_style": "CLASSIC",
                "serialnumber": "UNKNOWN",
                "model": "UNKNOWN",
                "vc_capable": False,
                "switch_style": "NONE",
                "personality": "UNKNOWN",
            },
        )

    @patch("jnpr.junos.transport.tty.sleep")
    @patch("ncclient.operations.rpc.RPCReply.parse")
    @patch("jnpr.junos.transport.tty_telnet.telnetlib.Telnet.write")
    @patch("jnpr.junos.transport.tty_netconf.select.select")
    @patch("jnpr.junos.transport.tty_telnet.telnetlib.Telnet.read_until")
    def test_load_console(
        self, mock_read_until, mock_select, mock_write, mock_parse, mock_sleep
    ):
        mock_select.return_value = ([self.dev._tty._rx], [], [])
        xml = """<policy-options>
                  <policy-statement>
                    <name>F5-in</name>
                    <term>
                        <name>testing</name>
                        <then>
                            <accept/>
                        </then>
                    </term>
                    <from>
                        <protocol>mpls</protocol>
                    </from>
                </policy-statement>
                </policy-options>"""

        mock_read_until.return_value = six.b(
            """
        <rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" xmlns:junos="http://xml.juniper.net/junos/15.2I0/junos">
            <load-configuration-results>
            <ok/>
            </load-configuration-results>
            </rpc-reply>
            ]]>]]>"""
        )
        cu = Config(self.dev)
        op = cu.load(xml, format="xml")
        cu.commit()

    @patch("ncclient.operations.rpc.RPCReply.parse")
    @patch("jnpr.junos.transport.tty_netconf.tty_netconf._receive")
    @patch("jnpr.junos.transport.tty_telnet.Telnet.rawwrite")
    def test_console_rpc_call(self, mock_write, mock_rcv, mock_parse):
        self.dev._tty.nc.rpc = MagicMock(side_effect=self._mock_manager)
        op = self.dev.rpc.get_chassis_inventory()
        self.assertEqual(op.tag, "chassis-inventory")

    @patch("ncclient.operations.rpc.RPCReply.parse")
    @patch("jnpr.junos.transport.tty_netconf.tty_netconf._receive")
    @patch("jnpr.junos.transport.tty_telnet.Telnet.rawwrite")
    def test_console_rpc_call_exception(self, mock_write, mock_rcv, mock_parse):
        mock_rcv.return_value = "<output>testing</output>"
        op = self.dev.rpc.get_chassis_inventory()
        self.assertEqual(op.tag, "output")

    def test_timeout_getter_setter(self):
        self.dev.timeout = 1
        self.assertEqual(1, self.dev.timeout)

    # below 2 function will be used in future.
    def _mock_manager(self, *args, **kwargs):
        if args:
            return self._read_file(etree.XML(args[0]).tag + ".xml")

    def _read_file(self, fname):
        from ncclient.xml_ import NCElement

        fpath = os.path.join(os.path.dirname(__file__), "rpc-reply", fname)
        with open(fpath) as fp:
            return fp.read()
