__author__ = "Stacy Smith"
__credits__ = "Jeremy Schulman, Nitin Kumar"

import unittest
from nose.plugins.attrib import attr
from mock import patch, MagicMock
import os
from lxml import etree

from jnpr.junos import Device
from jnpr.junos.exception import RpcError

from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession


@attr('unit')
class TestIfdStyle(unittest.TestCase):

    @patch('ncclient.manager.connect')
    def setUp(self, mock_connect):
        mock_connect.side_effect = self._mock_manager_setup
        self.dev = Device(host='1.1.1.1', user='rick', password='password123',
                          gather_facts=False)
        self.dev.open()

    @patch('jnpr.junos.Device.execute')
    def test_ifd_style_switch(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_ifd_style_switch
        self.assertEqual(self.dev.facts['ifd_style'],'SWITCH')

    @patch('jnpr.junos.Device.execute')
    def test_ifd_style_classic(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_ifd_style_classic
        self.assertEqual(self.dev.facts['ifd_style'],'CLASSIC')

    def _read_file(self, fname):
        from ncclient.xml_ import NCElement

        fpath = os.path.join(os.path.dirname(__file__),
                             'rpc-reply', fname)
        foo = open(fpath).read()

        rpc_reply = NCElement(foo,
                              self.dev._conn._device_handler
                              .transform_reply())._NCElement__doc[0]
        return rpc_reply

    def _mock_manager_setup(self, *args, **kwargs):
        if kwargs:
            device_params = kwargs['device_params']
            device_handler = make_device_handler(device_params)
            session = SSHSession(device_handler)
            return Manager(session, device_handler)

    def _mock_manager_ifd_style_classic(self, *args, **kwargs):
        if args:
            return self._read_file('ifd_style_classic_' + args[0].tag +
                                   '.xml')

    def _mock_manager_ifd_style_switch(self, *args, **kwargs):
        if args:
            if (args[0].tag == 'command'):
                raise RpcError()
            else:
                return self._read_file('ifd_style_switch_' + args[0].tag +
                                       '.xml')
