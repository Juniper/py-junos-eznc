__author__ = "Nitin Kumar, Rick Sherman"
__credits__ = "Jeremy Schulman"

import unittest
from nose.plugins.attrib import attr

from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos.exception import RpcError, LockError,\
    UnlockError, CommitError

from mock import MagicMock, patch
from lxml import etree


@attr('unit')
class TestConfig(unittest.TestCase):
    def setUp(self):
        self.dev = Device(host='1.1.1.1')
        self.conf = Config(self.dev)

    def test_config_constructor(self):
        self.assertTrue(isinstance(self.conf._dev, Device))

    def test_config_confirm(self):
        self.conf.rpc.commit_configuration = MagicMock()
        self.assertTrue(self.conf.commit(confirm=True))

    def test_config_commit_confirm_timeout(self):
        self.conf.rpc.commit_configuration = MagicMock()
        self.conf.commit(confirm=10)
        self.conf.rpc.commit_configuration\
            .assert_called_with(**{'confirm-timeout': '10', 'confirmed': True})

    def test_config_commit_comment(self):
        self.conf.rpc.commit_configuration = MagicMock()
        self.conf.commit(comment='Test')
        self.conf.rpc.commit_configuration.assert_called_with(log='Test')

    @patch('jnpr.junos.utils.config.JXML.remove_namespaces')
    def test_config_commit_exception(self, mock_jxml):
        class MyException(Exception):
            xml = 'test'
        self.conf.rpc.commit_configuration = \
            MagicMock(side_effect=MyException)
        self.assertRaises(AttributeError, self.conf.commit)

    def test_config_commit_exception_RpcError(self):
        ex = RpcError(rsp='ok')
        self.conf.rpc.commit_configuration = MagicMock(side_effect=ex)
        self.assertTrue(self.conf.commit())
        import xml.etree.ElementTree as ET
        xmldata = """<data><company name="Juniper">
            <code>pyez</code>
            <year>2013</year>
            </company></data>"""
        root = ET.fromstring(xmldata)
        el = root.find('company')
        ex = RpcError(rsp=el)
        self.conf.rpc.commit_configuration = MagicMock(side_effect=ex)
        self.assertRaises(CommitError, self.conf.commit)

    def test_commit_check(self):
        self.conf.rpc.commit_configuration = MagicMock()
        self.assertTrue(self.conf.commit_check())

    @patch('jnpr.junos.utils.config.JXML.rpc_error')
    def test_commit_check_exception(self, mock_jxml):
        class MyException(Exception):
                xml = 'test'
        self.conf.rpc.commit_configuration = MagicMock(side_effect=MyException)
        # with self.assertRaises(AttributeError):
        self.conf.commit_check()

    def test_config_commit_check_exception_RpcError(self):
        ex = RpcError(rsp='ok')
        self.conf.rpc.commit_configuration = MagicMock(side_effect=ex)
        self.assertTrue(self.conf.commit_check())
        import xml.etree.ElementTree as ET
        xmldata = """<data><company name="Juniper">
            <code>pyez</code>
            <year>2013</year>
            </company></data>"""
        root = ET.fromstring(xmldata)
        el = root.find('company')
        ex = RpcError(rsp=el)
        self.conf.rpc.commit_configuration = MagicMock(side_effect=ex)
        self.assertRaises(CommitError, self.conf.commit_check)

    def test_config_diff(self):
        self.conf.rpc.get_configuration = MagicMock()
        self.conf.diff()
        self.conf.rpc.get_configuration.\
            assert_called_with({'compare': 'rollback', 'rollback': '0', 'format': 'text'})

    def test_config_pdiff(self):
        self.conf.diff = MagicMock(return_value='Stuff')
        self.conf.pdiff()
        print self.conf.diff.call_args
        self.conf.diff.assert_called_once_with(0)

    def test_config_load(self):
        self.assertRaises(RuntimeError, self.conf.load)

    def test_config_load_vargs_len(self):
        self.assertRaises(RuntimeError, self.conf.load,
                          'test.xml')

    def test_config_load_len_with_format_set(self):
        self.conf.rpc.load_config = \
            MagicMock(return_value='rpc_contents')
        self.assertEqual(self.conf.load('test.xml', format='set'),
                         'rpc_contents')

    def test_config_load_len_with_format_xml(self):
        self.conf.rpc.load_config = \
            MagicMock(return_value='rpc_contents')
        xmldata = """<snmp>
          <community>
            <name>iBGP</name>
          </community>
        </snmp>"""

        self.assertEqual(self.conf.load(xmldata, format='xml'),
                         'rpc_contents')

    @patch('__builtin__.open')
    def test_config_load_lformat_byext_ValueError(self, mock_open):
        self.conf.rpc.load_config = \
            MagicMock(return_value='rpc_contents')
        self.assertRaises(ValueError, self.conf.load, path='test.jnpr')

    def test_config_load_lset_format_ValueError(self):
        self.conf.rpc.load_config = \
            MagicMock(return_value='rpc_contents')
        self.assertRaises(ValueError, self.conf.load,
                          'test.xml', format='set', overwrite=True)

    @patch('__builtin__.open')
    @patch('jnpr.junos.utils.config.etree.XML')
    def test_config_load_path_xml(self, mock_etree, mock_open):
        self.conf.dev.Template = MagicMock()
        mock_etree.return_value = 'rpc_contents'
        self.conf.rpc.load_config = \
            MagicMock(return_value=mock_etree.return_value)
        self.assertEqual(self.conf.load(path='test.xml'), 'rpc_contents')

    @patch('__builtin__.open')
    def test_config_load_path_text(self, mock_open):
        self.conf.rpc.load_config = MagicMock()
        self.conf.load(path='test.conf')
        self.assertEqual(self.conf.rpc.load_config.call_args[1]['format'],
                         'text')

    @patch('__builtin__.open')
    def test_config_load_path_set(self, mock_open):
        self.conf.rpc.load_config = MagicMock()
        self.conf.load(path='test.set')
        self.assertEqual(self.conf.rpc.load_config.call_args[1]['action'],
                         'set')

    @patch('__builtin__.open')
    def test_config_load_try_load_exception(self, mock_open):
        ex = RpcError(
            rsp = [etree.fromstring((
                """<load-configuration-results>
                <rpc-error>
                <error-severity>error</error-severity>
                <error-message>syntax error</error-message>
                </rpc-error>
                </load-configuration-results>"""))])
        self.conf.rpc.load_config = MagicMock(side_effect=ex)
        self.assertRaises(RpcError, self.conf.load, path='config.conf')


    @patch('jnpr.junos.utils.config.etree.XML')
    def test_config_load_template_path(self, mock_etree):
        self.conf.rpc.load_config = MagicMock()
        self.conf.dev.Template = MagicMock()
        self.conf.load(template_path='test.xml')
        self.assertEqual(self.conf.rpc.load_config.call_args[1]['format'],
                         'xml')

    def test_config_load_template(self):
        class Temp:
            filename = 'abc.xml'
            render = MagicMock(return_value='<test/>')
        self.conf.rpc.load_config = MagicMock()
        self.conf.load(template=Temp)
        self.assertEqual(self.conf.rpc.load_config.call_args[1]['format'],
                         'xml')

    def test_config_diff_exception(self):
        self.conf.rpc.get_configuration = MagicMock()
        self.assertRaises(ValueError, self.conf.diff, 51)
        self.assertRaises(ValueError, self.conf.diff, -1)

    def test_config_lock(self):
        self.conf.rpc.lock_configuration = MagicMock()
        self.assertTrue(self.conf.lock())

    @patch('jnpr.junos.utils.config.JXML.rpc_error')
    def test_config_lock_LockError(self, mock_jxml):
        ex = RpcError(rsp='ok')
        self.conf.rpc.lock_configuration = MagicMock(side_effect=ex)
        self.assertRaises(LockError, self.conf.lock)

    @patch('jnpr.junos.utils.config.JXML.remove_namespaces')
    def test_config_lock_exception(self, mock_jxml):
        class MyException(Exception):
                xml = 'test'
        self.conf.rpc.lock_configuration = MagicMock(side_effect=MyException)
        self.assertRaises(LockError, self.conf.lock)

    def test_config_unlock(self):
        self.conf.rpc.unlock_configuration = MagicMock()
        self.assertTrue(self.conf.unlock())

    @patch('jnpr.junos.utils.config.JXML.rpc_error')
    def test_config_unlock_LockError(self, mock_jxml):
        ex = RpcError(rsp='ok')
        self.conf.rpc.unlock_configuration = MagicMock(side_effect=ex)
        self.assertRaises(UnlockError, self.conf.unlock)

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

    @patch('jnpr.junos.Device.execute')
    def test_rescue_action_save(self, mock_exec):
        self.dev.request_save_rescue_configuration = MagicMock()
        self.assertTrue(self.conf.rescue('save'))

    @patch('jnpr.junos.Device.execute')
    def test_rescue_action_get_exception(self, mock_exec):
        self.dev.rpc.get_rescue_information = MagicMock(side_effect=Exception)
        self.assertTrue(self.conf.rescue('get')==None)

    @patch('jnpr.junos.Device.execute')
    def test_rescue_action_get(self, mock_exec):
        self.dev.rpc.get_rescue_information = MagicMock()
        self.dev.rpc.get_rescue_information.return_value = 1
        self.assertEqual(self.conf.rescue('get', format='xml'), 1)

    @patch('jnpr.junos.Device.execute')
    def test_rescue_action_delete(self, mock_exec):
        self.dev.rpc.request_delete_rescue_configuration = MagicMock()
        self.assertTrue(self.conf.rescue('delete'))

    @patch('jnpr.junos.Device.execute')
    def test_rescue_action_reload(self, mock_exec):
        self.dev.rpc.load_configuration = MagicMock()
        self.dev.rpc.load_configuration.return_value = True
        self.assertTrue(self.conf.rescue('reload'))

    @patch('jnpr.junos.Device.execute')
    def test_rescue_action_reload_exception(self, mock_exec):
        self.dev.rpc.load_configuration = MagicMock(side_effect=Exception)
        self.assertFalse(self.conf.rescue('reload'))

    @patch('jnpr.junos.Device.execute')
    def test_rescue_action_unsupported_action(self, mock_exec):
        self.assertRaises(ValueError, self.conf.rescue, 'abc')

    def test_config_load_lset_from_rexp_xml(self):
        self.conf.rpc.load_config = MagicMock()
        conf = """<snmp><name>iBGP</name></snmp>"""
        self.conf.load(conf)
        self.assertEqual(self.conf.rpc.load_config.call_args[1]['format'],
                         'xml')

    def test_config_load_lset_from_rexp_set(self):
        self.conf.rpc.load_config = MagicMock()
        conf = """set system domain-name englab.nitin.net"""
        self.conf.load(conf)
        self.assertEqual(self.conf.rpc.load_config.call_args[1]['format'],
                         'text')

    def test_config_load_lset_from_rexp_set_set(self):
        self.conf.rpc.load_config = MagicMock()
        conf = """set system domain-name englab.nitin.net"""
        self.conf.load(conf)
        self.assertEqual(self.conf.rpc.load_config.call_args[1]['format'],
                         'text')

    def test_config_load_lset_from_rexp_set_delete(self):
        self.conf.rpc.load_config = MagicMock()
        conf = """delete snmp"""
        self.conf.load(conf)
        self.assertEqual(self.conf.rpc.load_config.call_args[1]['format'],
                         'text')

    def test_config_load_lset_from_rexp_conf(self):
        self.conf.rpc.load_config = MagicMock()
        conf = """
            snmp {
                location USA;
                community iBGP {
                authorization read-only;
            }
            }"""
        self.conf.load(conf)
        self.assertEqual(self.conf.rpc.load_config.call_args[1]['format'],
                         'text')

    def test_config_load_lset_from_rexp_conf_replace_tag(self):
        self.conf.rpc.load_config = MagicMock()
        conf = """replace:
            snmp {
                location USA;
                community iBGP {
                authorization read-only;
            }
            }"""
        self.conf.load(conf)
        self.assertEqual(self.conf.rpc.load_config.call_args[1]['format'],
                         'text')

    def test_config_load_lset_from_rexp_error(self):
        self.conf.rpc.load_config = MagicMock()
        conf = """nitin>"""
        self.assertRaises(RuntimeError, self.conf.load, conf)