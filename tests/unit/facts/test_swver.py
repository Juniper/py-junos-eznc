__author__ = "Nitin Kumar, Rick Sherman"
__credits__ = "Jeremy Schulman"

import unittest
from nose.plugins.attrib import attr
from mock import patch
import os

from jnpr.junos import Device
from jnpr.junos.facts.swver import facts_software_version as software_version, version_info
from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession


@attr('unit')
class TestVersionInfo(unittest.TestCase):

    def test_version_info_after_type_len_else(self):
        self.assertEqual(version_info('12.1X46-D10').build, None)

    def test_version_info_constructor_else_exception(self):
        self.assertEqual(version_info('11.4R7').build, '7')

    def test_version_info_repr(self):
        self.assertEqual(repr(version_info('11.4R7.5')),
                         'junos.version_info(major=(11, 4), '
                         'type=R, minor=7, build=5)')

    def test_version_info_lt(self):
        self.assertTrue(version_info('13.3-20131120') < (14, 1))

    def test_version_info_lt_eq(self):
        self.assertTrue(version_info('13.3-20131120') <= (14, 1))

    def test_version_info_gt(self):
        self.assertTrue(version_info('13.3-20131120') > (12, 1))

    def test_version_info_gt_eq(self):
        self.assertTrue(version_info('13.3-20131120') >= (12, 1))

    def test_version_info_eq(self):
        self.assertEqual(version_info('13.3-20131120'), (13, 3))

    def test_version_info_not_eq(self):
        self.assertNotEqual(version_info('13.3-20131120'), (15, 3))


@attr('unit')
class TestSrxCluster(unittest.TestCase):

    @patch('ncclient.manager.connect')
    def setUp(self, mock_connect):
        mock_connect.side_effect = self._mock_manager
        self.dev = Device(host='1.1.1.1', user='rick', password='password123',
                          gather_facts=False)
        self.dev.open()
        self.facts = {}

    @patch('jnpr.junos.Device.execute')
    def test_swver(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.facts['master'] = 'RE0'
        software_version(self.dev, self.facts)
        self.assertEqual(self.facts['version'], '12.3R6.6')

    @patch('jnpr.junos.Device.execute')
    def test_swver_f_master_list(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.facts['master'] = ['RE0', 'RE1']
        software_version(self.dev, self.facts)
        self.assertEqual(self.facts['version'], '12.3R6.6')

    @patch('jnpr.junos.Device.execute')
    def test_swver_hostname_none(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.facts['master'] = 'RE5'
        self.facts['version_RE5'] = '15.3R6.6'
        software_version(self.dev, self.facts)
        self.assertEqual(self.facts['version'], '15.3R6.6')

# --> JLS, there should always be a facts['master'] assigned.
    # @patch('jnpr.junos.Device.execute')
    # def test_swver_master_none(self, mock_execute):
    #     mock_execute.side_effect = self._mock_manager
    #     self.facts['master'] = None
    #     software_version(self.dev, self.facts)
    #     self.assertEqual(self.facts['version'], '12.3R6.6')

    @patch('jnpr.junos.Device.execute')
    @patch('jnpr.junos.facts.swver.re.findall')
    def test_swver_exception_handling(self, mock_re_findall, mock_execute):
        mock_execute.side_effect = self._mock_manager
        mock_re_findall.side_effect = IndexError
        self.facts['master'] = 'RE0'
        software_version(self.dev, self.facts)
        self.assertEqual(self.facts['version'], '0.0I0.0')

    def _read_file(self, fname):
        from ncclient.xml_ import NCElement

        fpath = os.path.join(os.path.dirname(__file__),
                             'rpc-reply', fname)
        foo = open(fpath).read()

        rpc_reply = NCElement(foo, self.dev._conn.
                              _device_handler.transform_reply())\
            ._NCElement__doc[0]
        return rpc_reply

    def _mock_manager(self, *args, **kwargs):
        if kwargs:
            device_params = kwargs['device_params']
            device_handler = make_device_handler(device_params)
            session = SSHSession(device_handler)
            return Manager(session, device_handler)

        if args:
            return self._read_file(args[0].tag + '.xml')
