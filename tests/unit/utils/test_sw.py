from __future__ import print_function
import os
import sys
from six import StringIO
import unittest2 as unittest
from nose.plugins.attrib import attr
from contextlib import contextmanager
from jnpr.junos import Device
from jnpr.junos.exception import RpcError, SwRollbackError, RpcTimeoutError
from jnpr.junos.utils.sw import SW
from jnpr.junos.facts.swver import version_info
from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession
from lxml import etree
from mock import patch, MagicMock, call, mock_open

if sys.version < '3':
    builtin_string = '__builtin__'
else:
    builtin_string = 'builtins'

__author__ = "Nitin Kumar, Rick Sherman"
__credits__ = "Jeremy Schulman"

facts = {'domain': None, 'hostname': 'firefly', 'ifd_style': 'CLASSIC',
         'version_info': version_info('12.1X46-D15.3'),
         '2RE': True, 'serialnumber': 'aaf5fe5f9b88', 'fqdn': 'firefly',
         'virtual': True, 'switch_style': 'NONE', 'version': '12.1X46-D15.3',
         'HOME': '/cf/var/home/rick', 'srx_cluster': False,
         'version_RE0': '16.1-20160925.0',
         'version_RE1': '16.1-20160925.0',
         'model': 'FIREFLY-PERIMETER',
         'RE0': {'status': 'Testing',
                 'last_reboot_reason': 'Router rebooted after a '
                 'normal shutdown.',
                 'model': 'FIREFLY-PERIMETER RE',
                 'up_time': '6 hours, 29 minutes, 30 seconds'},
         'vc_capable': False, 'personality': 'SRX_BRANCH'}


@attr('unit')
class TestSW(unittest.TestCase):

    @patch('ncclient.manager.connect')
    def setUp(self, mock_connect):
        mock_connect.side_effect = self._mock_manager
        self.dev = Device(host='1.1.1.1', user='rick', password='password123',
                          gather_facts=False)
        self.dev.open()
        self.dev.facts = facts
        self.sw = self.get_sw()

    @patch('jnpr.junos.Device.execute')
    def get_sw(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        return SW(self.dev)

    @patch('ncclient.operations.session.CloseSession.request')
    def tearDown(self, mock_session):
        self.dev.close()

    def test_sw_hashfile(self):
        with patch(builtin_string + '.open', mock_open(), create=True):
            import jnpr.junos.utils.sw
            with open('foo') as h:
                h.read.side_effect = ('abc', 'a', '')
                jnpr.junos.utils.sw._hashfile(h, MagicMock())
                self.assertEqual(h.read.call_count, 3)

    @patch('jnpr.junos.Device.execute')
    def test_sw_constructor_multi_re(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.sw = SW(self.dev)
        self.assertTrue(self.sw._multi_RE)

    @patch('jnpr.junos.Device.execute')
    def test_sw_constructor_multi_vc(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.sw = SW(self.dev)
        self.assertFalse(self.sw._multi_VC)

    @patch(builtin_string + '.open')
    def test_sw_local_sha256(self, mock_built_open):
        package = 'test.tgz'
        self.assertEqual(SW.local_sha256(package),
                         'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934'
                         'ca495991b7852b855')

    @patch(builtin_string + '.open')
    def test_sw_local_md5(self, mock_built_open):
        package = 'test.tgz'
        self.assertEqual(self.sw.local_md5(package),
                         'd41d8cd98f00b204e9800998ecf8427e')

    @patch(builtin_string + '.open')
    def test_sw_local_sha1(self, mock_built_open):
        package = 'test.tgz'
        self.assertEqual(SW.local_sha1(package),
                         'da39a3ee5e6b4b0d3255bfef95601890afd80709')

    def test_sw_progress(self):
        with self.capture(SW.progress, self.dev, 'running') as output:
            self.assertEqual('1.1.1.1: running\n', output)

    def test_sw_progress(self):
        with self.capture(SW.progress, self.dev, 'running') as output:
            self.assertEqual('1.1.1.1: running\n', output)

    @patch('jnpr.junos.Device.execute')
    @patch('paramiko.SSHClient')
    @patch('scp.SCPClient.put')
    def test_sw_progress_true(self, scp_put, mock_paramiko, mock_execute):
        mock_execute.side_effect = self._mock_manager
        with self.capture(SW.progress, self.dev, 'testing') as output:
            self.sw.install('test.tgz', progress=True, checksum=345,
                            cleanfs=False)
            self.assertEqual('1.1.1.1: testing\n', output)

    @patch('paramiko.SSHClient')
    @patch('scp.SCPClient.put')
    def test_sw_put(self, mock_scp_put, mock_scp):
        package = 'test.tgz'
        self.sw.put(package)
        self.assertTrue(
            call(
                'test.tgz',
                '/var/tmp') in mock_scp_put.mock_calls)

    @patch('jnpr.junos.utils.sw.FTP')
    def test_sw_put_ftp(self, mock_ftp_put):
        dev = Device(host='1.1.1.1', user='rick', password='password123',
                     mode='telnet', port=23, gather_facts=False)
        sw = SW(dev)
        sw.put(package='test.tgz')
        self.assertTrue(
            call(
                'test.tgz',
                '/var/tmp') in mock_ftp_put.mock_calls)

    @patch('jnpr.junos.utils.scp.SCP.__exit__')
    @patch('jnpr.junos.utils.scp.SCP.__init__')
    @patch('jnpr.junos.utils.scp.SCP.__enter__')
    def test_sw_put_progress(self, mock_enter, mock_scp, mock_exit):
        package = 'test.tgz'
        mock_scp.side_effect = self._fake_scp
        with self.capture(self.sw.put, package, progress=self._my_scp_progress) as output:
            self.assertEqual('test.tgz 100 50\n', output)

    def _fake_scp(self, *args, **kwargs):
        progress = kwargs['progress']
        progress('test.tgz', 100, 50)

    @patch('jnpr.junos.Device.execute')
    def test_sw_pkgadd(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        package = 'test.tgz'
        self.assertTrue(self.sw.pkgadd(package))

    @patch('jnpr.junos.Device.execute')
    def test_sw_install_single_re(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.sw._multi_RE = False
        self.assertTrue(self.sw.install('test.tgz', no_copy=True))

    @patch('jnpr.junos.Device.execute')
    def test_sw_install_issu(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        package = 'test.tgz'
        self.assertTrue(self.sw.install(package, issu=True, no_copy=True))

    @patch('jnpr.junos.Device.execute')
    def test_sw_install_nssu(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        package = 'test.tgz'
        self.assertTrue(self.sw.install(package, nssu=True, no_copy=True))

    @patch('jnpr.junos.Device.execute')
    def test_sw_install_issu_nssu_both_error(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        try:
            self.sw.install('test.tgz', issu=True, nssu=True)
        except TypeError as ex:
            self.assertEqual(
                str(ex),
                'install function can either take issu or nssu not both')

    @patch('jnpr.junos.Device.execute')
    def test_sw_install_issu_single_re_error(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.sw._multi_RE = False
        try:
            self.sw.install('test.tgz', issu=True)
        except TypeError as ex:
            self.assertEqual(str(ex), 'ISSU/NSSU requires Multi RE setup')

    @patch('jnpr.junos.Device.execute')
    def test_sw_install_issu_nssu_single_re_error(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        package = 'test.tgz'
        self.sw._multi_RE = False
        self.assertRaises(TypeError, self.sw.install, package,
                          nssu=True, issu=True)

    @patch('jnpr.junos.Device.execute')
    def test_sw_pkgaddISSU(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        package = 'test.tgz'
        self.assertTrue(self.sw.pkgaddISSU(package))

    @patch('jnpr.junos.Device.execute')
    def test_sw_pkgaddNSSU(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        package = 'test.tgz'
        self.assertTrue(self.sw.pkgaddNSSU(package))

    @patch('jnpr.junos.Device.execute')
    def test_sw_pkgadd_pkg_set(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        pkg_set = ['abc.tgz', 'pqr.tgz']
        self.sw._mixed_VC = True
        self.sw.pkgadd(pkg_set)
        self.assertEqual([i.text for i in
                          mock_execute.call_args[0][0].findall('set')],
                         pkg_set)

    @patch('jnpr.junos.Device.execute')
    def test_sw_validate(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.assertTrue(self.sw.validate('package.tgz'))

    @patch('jnpr.junos.Device.execute')
    def test_sw_validate_nssu(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.sw.log = MagicMock()
        # get_config returns false
        self.assertFalse(self.sw.validate('package.tgz', nssu=True))
        self.sw.log.assert_called_with(
            'Requirement FAILED: GRES is not Enabled in configuration')

    @patch('jnpr.junos.Device.execute')
    def test_sw_validate_issu(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.dev.rpc.get_config = MagicMock()
        self.assertTrue(self.sw.validate('package.tgz', issu=True))

    @patch('jnpr.junos.Device.execute')
    def test_sw_val_issu_request_shell_execute_gres_on(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.dev.rpc.get_config = MagicMock()
        self.dev.rpc.request_shell_execute = MagicMock()
        self.dev.rpc.request_shell_execute.return_value = etree.fromstring(
            """<rpc-reply>
        <output>Graceful switchover: On</output>
        </rpc-reply>""")
        self.assertTrue(self.sw.validate('package.tgz', issu=True))

    @patch('jnpr.junos.Device.execute')
    def test_sw_validate_issu_2re_false(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.dev.facts['2RE'] = False
        self.assertFalse(self.sw.validate('package.tgz', issu=True))
        self.dev.facts['2RE'] = True

    @patch('paramiko.SSHClient')
    @patch('jnpr.junos.utils.start_shell.StartShell.wait_for')
    def test_sw_validate_issu_request_shell_execute(self, mock_ss,
                                                    mock_ssh):
        self._issu_test_helper()
        with patch('jnpr.junos.utils.start_shell.StartShell.run') as ss:
            ss.return_value = (True, 'Graceful switchover: On')
            self.assertTrue(self.sw.validate('package.tgz', issu=True))

    @patch('paramiko.SSHClient')
    @patch('jnpr.junos.utils.start_shell.StartShell.wait_for')
    def test_sw_validate_issu_ss_login_other_re_fail(self, mock_ss,
                                                     mock_ssh):
        self._issu_test_helper()
        with patch('jnpr.junos.utils.start_shell.StartShell.run') as ss:
            ss.return_value = (False, 'Graceful switchover: On')
            self.assertFalse(self.sw.validate('package.tgz', issu=True))
        self.sw.log.assert_called_with(
            'Requirement FAILED: Not able run "show system switchover"')

    @patch('paramiko.SSHClient')
    @patch('jnpr.junos.utils.start_shell.StartShell.wait_for')
    def test_sw_validate_issu_ss_graceful_off(self, mock_ss,
                                              mock_ssh):
        self._issu_test_helper()
        with patch('jnpr.junos.utils.start_shell.StartShell.run') as ss:
            ss.return_value = (True, 'Graceful switchover: Off')
            self.assertFalse(self.sw.validate('package.tgz', issu=True))
        self.sw.log.assert_called_with(
            'Requirement FAILED: Graceful switchover status is not On')

    def _issu_test_helper(self):
        self.sw.log = MagicMock()
        self.dev.rpc.request_shell_execute = MagicMock()
        self.dev.rpc = MagicMock()
        self.dev.rpc.get_routing_task_replication_state.return_value = \
            self._read_file('get-routing-task-replication-state.xml')
        self.dev.rpc.check_in_service_upgrade.return_value = \
            self._read_file('check-in-service-upgrade.xml')
        self.dev.rpc.request_shell_execute.side_effect = \
            RpcError(rsp='not ok')

    @patch('jnpr.junos.Device.execute')
    def test_sw_validate_issu_stateful_replication_off(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.dev.rpc.get_config = MagicMock()
        self.dev.rpc.get_routing_task_replication_state = MagicMock()
        self.sw.log = MagicMock()
        self.assertFalse(self.sw.validate('package.tgz', issu=True))
        self.sw.log.assert_called_with(
            'Requirement FAILED: Either Stateful Replication is not Enabled or RE mode\nis not Master')

    @patch('jnpr.junos.Device.execute')
    def test_sw_validate_issu_commit_sync_off(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.dev.rpc.get_config = MagicMock()
        self.dev.rpc.get_config.return_value = etree.fromstring("""
        <configuration>
            <chassis>
                <redundancy>
                    <graceful-switchover>
                    </graceful-switchover>
                </redundancy>
            </chassis>
        </configuration>""")
        self.sw.log = MagicMock()
        self.assertFalse(self.sw.validate('package.tgz', issu=True))
        self.sw.log.assert_called_with(
            'Requirement FAILED: commit synchronize is not Enabled in configuration')

    @patch('jnpr.junos.Device.execute')
    def test_sw_validate_issu_nonstop_routing_off(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.dev.rpc.get_config = MagicMock()
        self.dev.rpc.get_config.side_effect = iter([etree.fromstring("""
        <configuration>
            <chassis>
                <redundancy>
                    <graceful-switchover>
                    </graceful-switchover>
                </redundancy>
            </chassis>
        </configuration>"""), etree.fromstring("""
        <configuration>
            <system>
                <commit>
                    <synchronize/>
                </commit>
            </system>
        </configuration>"""), etree.fromstring("""<configuration>
        <routing-options></routing-options>
        </configuration>""")])
        self.sw.log = MagicMock()
        self.assertFalse(self.sw.validate('package.tgz', issu=True))
        self.sw.log.assert_called_with(
            'Requirement FAILED: NSR is not Enabled in configuration')

    @patch('jnpr.junos.Device.execute')
    def test_sw_validate_issu_validation_succeeded(self, mock_execute):
        rpc_reply = """<rpc-reply><output>mgd: commit complete
                        Validation succeeded
                        </output>
                        <package-result>1</package-result>
                        </rpc-reply>"""
        mock_execute.side_effect = etree.fromstring(rpc_reply)
        package = 'package.tgz'
        self.assertFalse(self.sw.validate(package, issu=True))

    @patch('jnpr.junos.Device.execute')
    def test_sw_remote_checksum_not_found(self, mock_execute):
        xml = '''<rpc-error>
        <error-severity>error</error-severity>
        <error-message>
        md5: /var/tmp/123: No such file or directory
        </error-message>
        </rpc-error>'''
        mock_execute.side_effect = RpcError(rsp=etree.fromstring(xml))
        package = 'test.tgz'
        self.assertEqual(self.sw.remote_checksum(package), None)

    @patch('jnpr.junos.Device.execute')
    def test_sw_remote_checksum_not_rpc_error(self, mock_execute):
        xml = '''<rpc-error>
        <error-severity>error</error-severity>
        <error-message>
        something else!
        </error-message>
        </rpc-error>'''
        mock_execute.side_effect = RpcError(rsp=etree.fromstring(xml))
        package = 'test.tgz'
        with self.assertRaises(RpcError):
            self.sw.remote_checksum(package)

    @patch('jnpr.junos.Device.execute')
    def test_sw_safe_copy(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        package = 'safecopy.tgz'
        self.sw.put = MagicMock()
        with patch('jnpr.junos.utils.sw.SW.local_md5'):
            self.assertTrue(self.sw.safe_copy(package, progress=self._myprogress,
                                              cleanfs=True,
                                              checksum='96a35ab371e1ca10408c3caecdbd8a67'))

    @patch('jnpr.junos.Device.execute')
    def test_sw_safe_copy_return_false(self, mock_execute):
        # not passing checksum value, will get random from magicmock
        mock_execute.side_effect = self._mock_manager
        package = 'safecopy.tgz'
        self.sw.put = MagicMock()
        with patch('jnpr.junos.utils.sw.SW.local_md5'):
            self.assertFalse(self.sw.safe_copy(package, progress=self._myprogress,
                                               cleanfs=True))

    @patch('jnpr.junos.Device.execute')
    def test_sw_safe_copy_checksum_none(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        package = 'safecopy.tgz'
        self.sw.put = MagicMock()
        with patch('jnpr.junos.utils.sw.SW.local_md5',
                   MagicMock(return_value='96a35ab371e1ca10408c3caecdbd8a67')):
            self.assertTrue(self.sw.safe_copy(package, progress=self._myprogress,
                                              cleanfs=True))

    @patch('jnpr.junos.Device.execute')
    def test_sw_safe_install(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        package = 'install.tgz'
        self.sw.put = MagicMock()
        with patch('jnpr.junos.utils.sw.SW.local_md5',
                   MagicMock(return_value='96a35ab371e1ca10408c3caecdbd8a67')):
            self.assertTrue(
                self.sw.install(
                    package,
                    progress=self._myprogress,
                    cleanfs=True))

    @patch('jnpr.junos.utils.sw.SW.safe_copy')
    def test_sw_safe_install_copy_fail(self, mock_copy):
        mock_copy.return_value = False
        self.assertFalse(self.sw.install('file'))

    @patch('jnpr.junos.utils.sw.SW.validate')
    def test_sw_install_validate(self, mock_validate):
        mock_validate.return_value = False
        self.assertFalse(self.sw.install('file', validate=True, no_copy=True))

    @patch(builtin_string+'.print')
    @patch('jnpr.junos.utils.sw.SW.pkgadd')
    def test_sw_install_multi_mx(self, mock_pkgadd, mock_print):
        mock_pkgadd.return_value = True
        self.sw._multi_RE = True
        self.sw._multi_MX = True
        self.assertTrue(self.sw.install('file', no_copy=True, progress=True))

    @patch('jnpr.junos.utils.sw.SW.pkgadd')
    def test_sw_install_multi_vc(self, mock_pkgadd):
        mock_pkgadd.return_value = True
        self.sw._multi_RE = True
        self.sw._multi_VC = True
        self.sw._RE_list = ('version_RE0', 'version_RE1')
        self.assertTrue(self.sw.install('file', no_copy=True))

    @patch('jnpr.junos.utils.sw.SW.pkgadd')
    def test_sw_install_mixed_vc(self, mock_pkgadd):
        mock_pkgadd.return_value = True
        self.sw._mixed_VC = True
        self.sw._RE_list = ('version_RE0', 'version_RE1')
        self.assertTrue(self.sw.install(pkg_set=['abc.tgz', 'pqr.tgz'],
                                        no_copy=True))

    @patch('jnpr.junos.utils.sw.SW.pkgadd')
    def test_sw_install_multi_vc_mode_disabled(self, mock_pkgadd):
        mock_pkgadd.return_value = True
        self.dev._facts = {'2RE': True,
                           'domain': None, 'RE1': {
                               'status': 'OK', 'model': 'RE-EX8208',
                               'mastership_state': 'backup'}, 'ifd_style': 'SWITCH',
                           'version_RE1': '12.3R7.7', 'version_RE0': '12.3',
                           'serialnumber': 'XXXXXX', 'fqdn': 'XXXXXX',
                           'RE0': {'status': 'OK', 'model': 'RE-EX8208',
                                   'mastership_state': 'master'}, 'switch_style': 'VLAN',
                           'version': '12.3R5-S3.1', 'master': 'RE0', 'hostname': 'XXXXXX',
                           'HOME': '/var/home/sn', 'vc_mode': 'Disabled', 'model': 'EX8208',
                           'vc_capable': True, 'personality': 'SWITCH'}
        sw = self.get_sw()
        sw.install(package='abc.tgz', no_copy=True)
        self.assertFalse(sw._multi_VC)
        calls = [call('/var/tmp/abc.tgz', dev_timeout=1800, re0=True),
                 call('/var/tmp/abc.tgz', dev_timeout=1800, re1=True)]
        mock_pkgadd.assert_has_calls(calls)

    @patch('jnpr.junos.utils.sw.SW.pkgadd')
    def test_sw_install_mixed_vc_with_copy(self, mock_pkgadd):
        mock_pkgadd.return_value = True
        self.sw._mixed_VC = True
        self.sw.put = MagicMock()
        self.sw.remote_checksum = MagicMock(
            return_value='d41d8cd98f00b204e9800998ecf8427e')
        self.sw._RE_list = ('version_RE0', 'version_RE1')
        with patch('jnpr.junos.utils.sw.SW.local_md5',
                   MagicMock(return_value='d41d8cd98f00b204e9800998ecf8427e')):
            self.assertTrue(
                self.sw.install(
                    pkg_set=[
                        'install.tgz',
                        'install.tgz'],
                    cleanfs=False))

    @patch('jnpr.junos.utils.sw.SW.pkgadd')
    def test_sw_install_mixed_vc_safe_copy_false(self, mock_pkgadd):
        mock_pkgadd.return_value = True
        self.sw._mixed_VC = True
        self.sw.safe_copy = MagicMock(return_value=False)
        self.sw.remote_checksum = MagicMock(
            return_value='d41d8cd98f00b204e9800998ecf8427e')
        self.sw._RE_list = ('version_RE0', 'version_RE1')
        with patch('jnpr.junos.utils.sw.SW.local_md5',
                   MagicMock(return_value='d41d8cd98f00b204e9800998ecf8427e')):
            self.assertFalse(
                self.sw.install(
                    pkg_set=[
                        'install.tgz',
                        'install.tgz'],
                    cleanfs=False))

    @patch('jnpr.junos.utils.sw.SW.pkgadd')
    def test_sw_install_mixed_vc_ValueError(self, mock_pkgadd):
        mock_pkgadd.return_value = True
        self.sw._mixed_VC = True
        self.sw.remote_checksum = MagicMock(
            return_value='d41d8cd98f00b204e9800998ecf8427e')
        self.sw._RE_list = ('version_RE0', 'version_RE1')
        with patch('jnpr.junos.utils.sw.SW.local_md5',
                   MagicMock(return_value='d41d8cd98f00b204e9800998ecf8427e')):
            self.assertRaises(
                ValueError,
                self.sw.install,
                pkg_set='install.tgz',
                cleanfs=False)

    @patch('jnpr.junos.utils.sw.SW.pkgadd')
    def test_sw_install_mixed_vc_TypeError(self, mock_pkgadd):
        self.assertRaises(TypeError, self.sw.install, cleanfs=False)

    @patch('jnpr.junos.Device.execute')
    def test_sw_install_kwargs_force_host(self, mock_execute):
        self.sw.install('file', no_copy=True, force_host=True)
        rpc = [
            '<request-package-add><force-host/><no-validate/><re1/><package-name>/var/tmp/file</package-name></request-package-add>',
            '<request-package-add><package-name>/var/tmp/file</package-name><no-validate/><force-host/><re1/></request-package-add>',
            '<request-package-add><package-name>/var/tmp/file</package-name><no-validate/><re1/><force-host/></request-package-add>',
            '<request-package-add><force-host/><no-validate/><package-name>/var/tmp/file</package-name><re1/></request-package-add>',
            '<request-package-add><force-host/><re1/><no-validate/><package-name>/var/tmp/file</package-name></request-package-add>',
            '<request-package-add><no-validate/><re1/><package-name>/var/tmp/file</package-name><force-host/></request-package-add>',
            '<request-package-add><no-validate/><package-name>/var/tmp/file</package-name><force-host/><re1/></request-package-add>',
            '<request-package-add><force-host/><package-name>/var/tmp/file</package-name><no-validate/><re1/></request-package-add>',
            '<request-package-add><re1/><no-validate/><package-name>/var/tmp/file</package-name><force-host/></request-package-add>',
            '<request-package-add><re1/><force-host/><package-name>/var/tmp/file</package-name><no-validate/></request-package-add>',
            '<request-package-add><re1/><package-name>/var/tmp/file</package-name><force-host/><no-validate/></request-package-add>',
            '<request-package-add><re1/><force-host/><no-validate/><package-name>/var/tmp/file</package-name></request-package-add>',
            '<request-package-add><no-validate/><force-host/><re1/><package-name>/var/tmp/file</package-name></request-package-add>',
            '<request-package-add><package-name>/var/tmp/file</package-name><force-host/><no-validate/><re1/></request-package-add>',
            '<request-package-add><no-validate/><re1/><force-host/><package-name>/var/tmp/file</package-name></request-package-add>',
            '<request-package-add><package-name>/var/tmp/file</package-name><force-host/><re1/><no-validate/></request-package-add>',
            '<request-package-add><no-validate/><force-host/><package-name>/var/tmp/file</package-name><re1/></request-package-add>',
            '<request-package-add><force-host/><no-validate/><package-name>/var/tmp/file</package-name></request-package-add>',
            '<request-package-add><force-host/><package-name>/var/tmp/file</package-name><no-validate/></request-package-add>',
            '<request-package-add><package-name>/var/tmp/file</package-name><no-validate/><force-host/></request-package-add>',
            '<request-package-add><no-validate/><force-host/><package-name>/var/tmp/file</package-name></request-package-add>',
            '<request-package-add><no-validate/><package-name>/var/tmp/file</package-name><force-host/></request-package-add>',
            '<request-package-add><package-name>/var/tmp/file</package-name><force-host/><no-validate/></request-package-add>',
            '<request-package-add><package-name>/var/tmp/file</package-name><re1/><no-validate/><force-host/></request-package-add>',
            '<request-package-add><package-name>/var/tmp/file</package-name><re1/><force-host/><no-validate/></request-package-add>',
            '<request-package-add><force-host/><package-name>/var/tmp/file</package-name><re1/><no-validate/></request-package-add>',
            '<request-package-add><re1/><package-name>/var/tmp/file</package-name><no-validate/><force-host/></request-package-add>',
            '<request-package-add><no-validate/><package-name>/var/tmp/file</package-name><re1/><force-host/></request-package-add>',
            '<request-package-add><re1/><no-validate/><force-host/><package-name>/var/tmp/file</package-name></request-package-add>',
            '<request-package-add><force-host/><re1/><package-name>/var/tmp/file</package-name><no-validate/></request-package-add>']
        self.assertTrue(etree.tostring(
            mock_execute.call_args[0][0]).decode('utf-8') in rpc)

    @patch('jnpr.junos.Device.execute')
    def test_sw_rollback(self, mock_execute):
        rsp = '<rpc-reply><output>junos-vsrx-12.1X46-D30.2-domestic will become active at next reboot</output></rpc-reply>'
        mock_execute.side_effect = etree.XML(rsp)
        msg = 'junos-vsrx-12.1X46-D30.2-domestic will become active at next reboot'
        self.assertEqual(self.sw.rollback(), msg)

    @patch('jnpr.junos.Device.execute')
    def test_sw_rollback_multi(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        msg = {'fpc1': "Junos version 'D10.2' will become active at next reboot",
               'fpc0': 'JUNOS version "D10.2" will become active at next reboot'}
        self.assertEqual(eval(self.sw.rollback()), msg)

    @patch('jnpr.junos.Device.execute')
    def test_sw_rollback_multi_exception(self, mock_execute):
        fname = 'request-package-rollback-multi-error.xml'
        mock_execute.side_effect = self._read_file(fname)
        self.assertRaises(SwRollbackError, self.sw.rollback)

    @patch('jnpr.junos.Device.execute')
    def test_sw_rollback_exception(self, mock_execute):
        rsp = '<rpc-reply><output>WARNING: Cannot rollback, /packages/junos.old is not valid</output></rpc-reply>'
        mock_execute.side_effect = etree.XML(rsp)
        self.assertRaises(SwRollbackError, self.sw.rollback)

    def test_sw_inventory(self):
        self.sw.dev.rpc.file_list = \
            MagicMock(side_effect=self._mock_manager)
        self.assertEqual(
            self.sw.inventory, {
                'current': None, 'rollback': None})

    @patch('jnpr.junos.Device.execute')
    def test_sw_reboot(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.sw._multi_MX = True
        self.assertTrue('Shutdown NOW' in self.sw.reboot())

    @patch('jnpr.junos.Device.execute')
    def test_sw_reboot_at(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.assertTrue('Shutdown at' in self.sw.reboot(at='201407091815'))

    @patch('jnpr.junos.Device.execute')
    def test_sw_reboot_multi_re_vc(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.sw._multi_RE = True
        self.sw._multi_VC = False
        self.assertTrue('Shutdown NOW' in self.sw.reboot())

    @patch('jnpr.junos.Device.execute')
    def test_sw_reboot_mixed_vc(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.sw._mixed_VC = True
        self.sw._multi_VC = True
        self.sw.reboot()
        self.assertTrue('all-members' in
                        (etree.tostring(mock_execute.call_args[0][0]).decode('utf-8')))

    @patch('jnpr.junos.Device.execute')
    def test_sw_reboot_mixed_vc_all_re_false(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.sw._mixed_VC = True
        self.sw._multi_VC = True
        self.sw.reboot(all_re=False)
        self.assertTrue('all-members' not in
                        (etree.tostring(mock_execute.call_args[0][0]).decode('utf-8')))

    @patch('jnpr.junos.Device.execute')
    def test_sw_reboot_exception(self, mock_execute):
        rsp = etree.XML('<rpc-reply><a>test</a></rpc-reply>')
        mock_execute.side_effect = RpcError(rsp=rsp)
        self.assertRaises(Exception, self.sw.reboot)

    @patch('jnpr.junos.Device.execute')
    def test_sw_reboot_exception_RpcTimeoutError(self, mock_execute):
        rsp = (self.dev, 'request-reboot', 60)
        mock_execute.side_effect = RpcTimeoutError(*rsp)
        self.assertRaises(Exception, self.sw.reboot)

    @patch('jnpr.junos.Device.execute')
    def test_sw_poweroff(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.sw._multi_MX = True
        self.assertTrue('Shutdown NOW' in self.sw.poweroff())

    @patch('jnpr.junos.Device.execute')
    def test_sw_poweroff_exception(self, mock_execute):
        rsp = etree.XML('<rpc-reply><a>test</a></rpc-reply>')
        mock_execute.side_effect = RpcError(rsp=rsp)
        self.assertRaises(Exception, self.sw.poweroff)

    @patch('jnpr.junos.Device.execute')
    def test_sw_poweroff_multi_re_vc(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.sw._multi_RE = True
        self.sw._multi_VC = False
        self.assertTrue('Shutdown NOW' in self.sw.poweroff())

    def _myprogress(self, dev, report):
        pass

    def _my_scp_progress(self, _path, _total, _xfrd):
        print (_path, _total, _xfrd)

    @contextmanager
    def capture(self, command, *args, **kwargs):
        out, sys.stdout = sys.stdout, StringIO()
        command(*args, **kwargs)
        sys.stdout.seek(0)
        yield sys.stdout.read()
        sys.stdout = out

    def _read_file(self, fname):
        from ncclient.xml_ import NCElement

        fpath = os.path.join(os.path.dirname(__file__),
                             'rpc-reply', fname)
        foo = open(fpath).read()
        rpc_reply = NCElement(
            foo,
            self.dev._conn._device_handler.transform_reply())._NCElement__doc[0]
        return rpc_reply

    def _mock_manager(self, *args, **kwargs):
        if kwargs:
            # Little hack for mocked execute
            if 'dev_timeout' in kwargs:
                return self._read_file(args[0].tag + '.xml')
            if 'path' in kwargs:
                if kwargs['path'] == '/packages':
                    return self._read_file('file-list_dir.xml')
            device_params = kwargs['device_params']
            device_handler = make_device_handler(device_params)
            session = SSHSession(device_handler)
            return Manager(session, device_handler)

        elif args:
            if args[0].find('at') is not None:
                return self._read_file('request-reboot-at.xml')
            else:
                return self._read_file(args[0].tag + '.xml')
