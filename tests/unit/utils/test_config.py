__author__ = "Nitin Kumar, Rick Sherman"
__copyright__ = "Juniper networks"
__credits__ = "Jeremy Schulman"

import unittest

from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos.exception import RpcError, LockError, UnlockError

from mock import MagicMock, patch, PropertyMock

class TestConfig(unittest.TestCase):
    def setUp(self):
        self.dev = Device(host='1.1.1.1')
        self.conf = Config(self.dev)

    def test_config_constructor(self):
        self.assertIsInstance(self.conf._dev, Device)

    def test_config_confirm(self):
        self.conf.rpc.commit_configuration = MagicMock()
        self.assertTrue(self.conf.commit(confirm=True))

    @patch('jnpr.junos.utils.config.JXML.remove_namespaces')
    def test_config_commit_exception(self, mock_jxml):
        with self.assertRaises(AttributeError):
            class MyException(Exception):
                xml = 'test'
            self.conf.rpc.commit_configuration = MagicMock(side_effect=MyException)
            self.conf.commit()

    def test_config_commit_exception_RpcError(self):
        ex = RpcError(rsp='ok')
        self.conf.rpc.commit_configuration = MagicMock(side_effect=ex)
        self.assertTrue(self.conf.commit())
        ex = RpcError(rsp='not')
        self.conf.rpc.commit_configuration = MagicMock(side_effect=ex)
        with self.assertRaises(AttributeError):
            self.conf.commit()

    def test_commit_check(self):
        self.conf.rpc.commit_configuration = MagicMock()
        self.assertTrue(self.conf.commit_check())

    @patch('jnpr.junos.utils.config.JXML.remove_namespaces')
    def test_commit_check_exception(self, mock_jxml):
        class MyException(Exception):
                xml = 'test'
        self.conf.rpc.commit_configuration = MagicMock(side_effect=MyException)
        with self.assertRaises(AttributeError):
            self.conf.commit_check()

    def test_config_commit_check_exception_RpcError(self):
        ex = RpcError(rsp='ok')
        self.conf.rpc.commit_configuration = MagicMock(side_effect=ex)
        self.assertTrue(self.conf.commit_check())
        ex = RpcError(rsp='not')
        self.conf.rpc.commit_configuration = MagicMock(side_effect=ex)
        with self.assertRaises(AttributeError):
            self.conf.commit_check()

    def test_config_lock(self):
        self.conf.rpc.lock_configuration = MagicMock()
        self.assertTrue(self.conf.lock())

    @patch('jnpr.junos.utils.config.JXML.remove_namespaces')
    def test_config_lock_exception(self, mock_jxml):
        class MyException(Exception):
                xml = 'test'
        self.conf.rpc.lock_configuration = MagicMock(side_effect=MyException)
        self.assertRaises(LockError, self.conf.lock)

    def test_config_unlock(self):
        self.conf.rpc.unlock_configuration = MagicMock()
        self.assertTrue(self.conf.unlock())

    @patch('jnpr.junos.utils.config.JXML.remove_namespaces')
    def test_config_unlock_exception(self, mock_jxml):
        class MyException(Exception):
                xml = 'test'
        self.conf.rpc.unlock_configuration = MagicMock(side_effect=MyException)
        self.assertRaises(UnlockError, self.conf.unlock)

    def test_config_rollback(self):
        self.conf.rpc.load_configuration = MagicMock()
        self.assertTrue(self.conf.rollback())

    def test_config_rollback_exception(self):
        self.conf.rpc.load_configuration = MagicMock()
        self.assertRaises(ValueError, self.conf.rollback, 51)
        self.assertRaises(ValueError, self.conf.rollback, -1)