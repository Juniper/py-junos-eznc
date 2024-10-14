__author__ = "Stacy Smith"
__credits__ = "Jeremy Schulman, Nitin Kumar"

try:
    import unittest2 as unittest
except:
    import unittest
import nose2
from unittest.mock import patch, MagicMock
import os

from jnpr.junos import Device

from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession


class TestVmHost(unittest.TestCase):
    @patch("ncclient.manager.connect")
    def setUp(self, mock_connect):
        mock_connect.side_effect = self._mock_manager_setup
        self.dev = Device(
            host="1.1.1.1", user="rick", password="password123", gather_facts=False
        )
        self.dev.open()

    @patch("jnpr.junos.Device.execute")
    def test_vmhost_true(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_vmhost_true
        self.assertEqual(self.dev.facts["vmhost"], True)

    @patch("jnpr.junos.Device.execute")
    def test_vmhost_false(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_vmhost_false
        self.assertEqual(self.dev.facts["vmhost"], False)

    @patch("jnpr.junos.Device.execute")
    def test_vmhost_linux(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_vmhost_false
        self.dev.facts._cache["_is_linux"] = True
        self.assertEqual(self.dev.facts["vmhost"], False)

    @patch("jnpr.junos.Device.execute")
    def test_vmhost_error(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_vmhost_error
        self.assertEqual(self.dev.facts["vmhost"], None)

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

    def _mock_manager_vmhost_true(self, *args, **kwargs):
        if args:
            return self._read_file("vmhost_true_" + args[0].tag + ".xml")

    def _mock_manager_vmhost_false(self, *args, **kwargs):
        if args:
            return self._read_file("vmhost_false_" + args[0].tag + ".xml")

    def _mock_manager_vmhost_error(self, *args, **kwargs):
        if args:
            return self._read_file("vmhost_error_" + args[0].tag + ".xml")
