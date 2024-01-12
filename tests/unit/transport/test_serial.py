try:
    import unittest2 as unittest
except ImportError:
    import unittest
import nose2
from mock import MagicMock, patch
import sys
import six

from jnpr.junos.console import Console

if sys.version < "3":
    builtin_string = "__builtin__"
else:
    builtin_string = "builtins"


class TestSerial(unittest.TestCase):
    @patch("jnpr.junos.transport.tty_serial.serial.Serial.open")
    @patch("jnpr.junos.transport.tty_serial.serial.Serial.write")
    @patch("jnpr.junos.transport.tty_serial.serial.Serial.flush")
    @patch("jnpr.junos.transport.tty_serial.Serial.read_prompt")
    @patch("jnpr.junos.transport.tty.tty_netconf.open")
    def setUp(self, mock_nc_open, mock_read, mock_flush, mock_write, mock_open):
        self.dev = Console(port="USB/ttyUSB0", baud=9600, mode="Serial")
        mock_read.side_effect = [
            ("login", "login"),
            ("passwd", "passwd"),
            ("shell", "shell"),
        ]
        self.dev.open()

    @patch("jnpr.junos.transport.tty.sleep")
    @patch("jnpr.junos.transport.tty.tty_netconf.close")
    @patch("jnpr.junos.transport.tty_serial.Serial.read_prompt")
    @patch("jnpr.junos.transport.tty_serial.Serial.write")
    @patch("jnpr.junos.transport.tty_serial.Serial._tty_close")
    def tearDown(
        self, mock_serial_close, mock_write, mock_read, mock_close, mock_sleep
    ):
        mock_read.side_effect = [
            ("shell", "shell"),
            ("login", "login"),
            ("cli", "cli"),
        ]
        self.dev.close()

    def test_console_connected(self):
        self.assertTrue(self.dev.connected)

    def test_close_connection(self):
        self.dev._tty._ser = MagicMock()
        self.dev.close(skip_logout=True)
        self.assertTrue(self.dev._tty._ser.close.called)

    @patch("jnpr.junos.transport.tty_serial.serial.Serial.open")
    def test_tty_serial_open_exception(self, mock_open):
        dev = Console(port="USB/ttyUSB0", baud=9600, mode="Serial")
        mock_open.side_effect = OSError
        self.assertRaises(RuntimeError, dev.open)

    def test_tty_serial_rawwrite(self):
        self.dev._tty._ser = MagicMock()
        self.dev._tty.rawwrite("test")
        self.dev._tty._ser.write.assert_called_with("test")

    def test_tty_serial_read(self):
        self.dev._tty._ser = MagicMock()
        self.dev._tty.read()
        self.dev._tty._ser.readline.assert_called()

    def test_tty_serial_read_prompt(self):
        self.dev._tty._ser = MagicMock()
        self.dev._tty.EXPECT_TIMEOUT = 0.1
        self.dev._tty._ser.readline.side_effect = ["", "test"]
        self.assertEqual(self.dev._tty.read_prompt()[0], None)


class TestSerialWin(unittest.TestCase):
    @patch("jnpr.junos.transport.tty_serial.serial.Serial.open")
    @patch("jnpr.junos.transport.tty_serial.serial.Serial.read")
    @patch("jnpr.junos.transport.tty_serial.serial.Serial.write")
    @patch("jnpr.junos.transport.tty_serial.serial.Serial.flush")
    @patch("jnpr.junos.transport.tty_serial.Serial.read_prompt")
    def setUp(self, mock_read, mock_flush, mock_write, mock_serial_read, mock_open):
        self.dev = Console(port="COM4", baud=9600, mode="Serial")
        mock_read.side_effect = [
            ("login", "login"),
            ("passwd", "passwd"),
            ("shell", "shell"),
        ]
        mock_serial_read.side_effect = [
            six.b(
                "<!-- No zombies were killed during the creation of this user interface -->"
            ),
            six.b(""),
            six.b(
                """<!-- user root, class super-user -->
<hello xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <capabilities>
    <capability>urn:ietf:params:netconf:base:1.0</capability>
    <capability>urn:ietf:params:netconf:capability:candidate:1.0</capability>
    <capability>urn:ietf:params:netconf:capability:confirmed-commit:1.0</capability>
    <capability>urn:ietf:params:netconf:capability:validate:1.0</capability>
    <capability>urn:ietf:params:netconf:capability:url:1.0?scheme=http,ftp,file</capability>
    <capability>urn:ietf:params:xml:ns:netconf:base:1.0</capability>
    <capability>urn:ietf:params:xml:ns:netconf:capability:candidate:1.0</capability>
    <capability>urn:ietf:params:xml:ns:netconf:capability:confirmed-commit:1.0</capability>
    <capability>urn:ietf:params:xml:ns:netconf:capability:validate:1.0</capability>
    <capability>urn:ietf:params:xml:ns:netconf:capability:url:1.0?scheme=http,ftp,file</capability>
    <capability>urn:ietf:params:xml:ns:yang:ietf-netconf-monitoring</capability>
    <capability>http://xml.juniper.net/netconf/junos/1.0</capability>
    <capability>http://xml.juniper.net/dmi/system/1.0</capability>
  </capabilities>
  <session-id>7478</session-id>
</hello>
]]>]]>"""
            ),
            six.b(""),
        ]
        self.dev.open()

    @patch("jnpr.junos.transport.tty.sleep")
    @patch("jnpr.junos.transport.tty.tty_netconf.close")
    @patch("jnpr.junos.transport.tty_serial.Serial.read_prompt")
    @patch("jnpr.junos.transport.tty_serial.Serial.write")
    @patch("jnpr.junos.transport.tty_serial.Serial._tty_close")
    def tearDown(
        self, mock_serial_close, mock_write, mock_read, mock_close, mock_sleep
    ):
        mock_read.side_effect = [
            ("shell", "shell"),
            ("login", "login"),
            ("cli", "cli"),
        ]
        self.dev.close()

    def test_tty_serial_win_connected(self):
        self.assertTrue(self.dev.connected)

    @patch("jnpr.junos.transport.tty.tty_netconf.close")
    @patch("jnpr.junos.transport.tty_serial.Serial._tty_close")
    def test_tty_serial_win_rpc_call(self, mock_serial_close, mock_close):
        self.dev._tty.read = MagicMock()
        self.dev._tty.rawwrite = MagicMock()
        self.dev._tty.read.side_effect = [
            six.b(
                '<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"'
                ' xmlns:junos="http://xml.juniper.net/junos/15.1X49/junos">'
                '<route-engine-information xmlns="http://xml.juniper.net/ju'
                'nos/15.1X49/junos-chassis"><route-engine><status>OK</statu'
                's><temperature junos:celsius="45">45 degrees C / 113 degre'
                'es F</temperature><cpu-temperature junos:celsius="61">61 d'
                "egrees C / 141 degrees F</cpu-temperature><memory-system-t"
                "otal>4096</memory-system-total><memory-system-total-used>1"
                "024</memory-system-total-used><memory-system-total-util>25"
                "</memory-system-total-util><memory-control-plane>2624</mem"
                "ory-control-plane><memory-control-plane-used>682</memory-c"
                "ontrol-plane-used><memory-control-plane-util>26</memory-co"
                "ntrol-plane-util><memory-data-plane>1472</memory-data-plan"
                "e><memory-data-plane-used>353</memory-data-plane-used><mem"
                "ory-data-plane-util>24</memory-data-plane-util><cpu-user>1"
                "2</cpu-user><cpu-background>0</cpu-background><cpu-system>"
                "6</cpu-system><cpu-interrupt>0</cpu-interrupt><cpu-idle>83"
                "</cpu-idle><model>RE-SRX300</model><serial-number>CV0918AF"
                '1022</serial-number><start-time junos:seconds="1584539305"'
                ">2020-03-18 08:48:25 CDT</start-time><up-time junos:second"
                's="137925">1 day, 14 hours, 18 minutes, 45 seconds</up-tim'
                "e><last-reboot-reason>0x1:power cycle/failure</last-reboot"
                "-reason><load-average-one>0.12</load-average-one><load-ave"
                "rage-five>0.08</load-average-five><load-average-fifteen>0."
                "06</load-average-fifteen></route-engine></route-engine-inf"
                "ormation></rpc-reply>]]>]]>"
            )
        ]
        res = self.dev.rpc.get_route_engine_information()
        self.assertEqual(res.tag, "route-engine-information")
