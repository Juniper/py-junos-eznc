__author__ = "Nitin Kumar, Rick Sherman"
__credits__ = "Jeremy Schulman"

try:
    import unittest2 as unittest
except ImportError:
    import unittest
import nose2
from mock import patch, MagicMock
import os

from jnpr.junos import Device
from jnpr.junos.ofacts.swver import facts_software_version as software_version
from jnpr.junos.ofacts.swver import _get_swver
from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession
from jnpr.junos.exception import RpcError


class TestSwver(unittest.TestCase):
    @patch("ncclient.manager.connect")
    @patch("jnpr.junos.device.warnings")
    def setUp(self, mock_warnings, mock_connect):
        mock_connect.side_effect = self._mock_manager
        self.dev = Device(
            host="1.1.1.1",
            user="rick",
            password="password123",
            gather_facts=False,
            fact_style="old",
        )
        self.dev.open()
        self.facts = {}
        self.facts["vc_capable"] = False

    def test_get_swver_vc(self):
        self.dev.rpc.cli = MagicMock()
        self.facts["vc_capable"] = True
        _get_swver(self.dev, self.facts)
        self.dev.rpc.cli.assert_called_with("show version all-members", format="xml")

    def test_get_swver_vc_capable_standalone(self):
        def raise_ex(*args):
            if args[0] == "show version all-members":
                raise RpcError()

        self.dev.rpc.cli = MagicMock(
            side_effect=lambda *args, **kwargs: raise_ex(*args)
        )
        self.facts["vc_capable"] = True
        _get_swver(self.dev, self.facts)
        self.dev.rpc.cli.assert_called_with(
            "show version invoke-on all-routing-engines", format="xml"
        )

    @patch("jnpr.junos.Device.execute")
    def test_swver(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.facts["master"] = "RE0"
        software_version(self.dev, self.facts)
        self.assertEqual(self.facts["version"], "12.3R6.6")

    @patch("jnpr.junos.Device.execute")
    def test_swver_f_master_list(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.facts["master"] = ["RE0", "RE1"]
        software_version(self.dev, self.facts)
        self.assertEqual(self.facts["version"], "12.3R6.6")

    @patch("jnpr.junos.Device.execute")
    def test_swver_hostname_none(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.facts["master"] = "RE5"
        self.facts["version_RE5"] = "15.3R6.6"
        software_version(self.dev, self.facts)
        self.assertEqual(self.facts["version"], "15.3R6.6")

    @patch("jnpr.junos.Device.execute")
    def test_swver_txp_master_list(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.facts["master"] = ["RE0", "RE0", "RE1", "RE2", "RE3"]
        self.facts["version_RE0-RE0"] = "14.2R4"
        software_version(self.dev, self.facts)
        self.assertEqual(self.facts["version"], "14.2R4")

    # --> JLS, there should always be a facts['master'] assigned.
    # @patch('jnpr.junos.Device.execute')
    # def test_swver_master_none(self, mock_execute):
    #     mock_execute.side_effect = self._mock_manager
    #     self.facts['master'] = None
    #     software_version(self.dev, self.facts)
    #     self.assertEqual(self.facts['version'], '12.3R6.6')

    @patch("jnpr.junos.Device.execute")
    @patch("jnpr.junos.facts.get_software_information.re.findall")
    def test_swver_exception_handling(self, mock_re_findall, mock_execute):
        mock_execute.side_effect = self._mock_manager
        mock_re_findall.side_effect = IndexError
        self.facts["master"] = "RE0"
        software_version(self.dev, self.facts)
        self.assertEqual(self.facts["version"], "0.0I0.0")

    def _read_file(self, fname):
        from ncclient.xml_ import NCElement

        fpath = os.path.join(os.path.dirname(__file__), "rpc-reply", fname)
        foo = open(fpath).read()

        rpc_reply = NCElement(
            foo, self.dev._conn._device_handler.transform_reply()
        )._NCElement__doc[0]
        return rpc_reply

    def _mock_manager(self, *args, **kwargs):
        if kwargs:
            device_params = kwargs["device_params"]
            device_handler = make_device_handler(device_params)
            session = SSHSession(device_handler)
            return Manager(session, device_handler)

        if args:
            if "version_RE0-RE0" in self.facts:
                return self._read_file(args[0].tag + "_RE0-RE0.xml")
            return self._read_file(args[0].tag + ".xml")
