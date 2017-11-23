__author__ = "Nitin Kumar"
__credits__ = "Jeremy Schulman"

import unittest
import os
from nose.plugins.attrib import attr

from jnpr.junos import Device

from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession
from mock import MagicMock, patch


@attr('unit')
class TestFactoryCfgTable(unittest.TestCase):

    @patch('ncclient.manager.connect')
    def setUp(self, mock_connect):
        mock_connect.side_effect = self._mock_manager
        self.dev = Device(host='1.1.1.1', user='rick', password='password123',
                          gather_facts=False)
        self.dev.open()

    @patch('jnpr.junos.Device.execute')
    def test_unstructured_data(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        from jnpr.junos.command.cmerror import CMErrorTable
        stats = CMErrorTable(self.dev)
        stats = stats.get()
        self.assertEqual(dict(stats),
                         {1: {'errors': 0, 'name': 'PQ3 Chip'},
                          2: {'errors': 0, 'name': 'Host Loopback'},
                          3: {'errors': 0, 'name': 'CM[0]'},
                          4: {'errors': 0, 'name': 'CM[1]'},
                          5: {'errors': 0, 'name': 'LUCHIP(0)'},
                          6: {'errors': 0, 'name': 'TOE-LU-0:0:0'}})
        self.assertEqual(repr(stats), 'CMErrorTable:1.1.1.1: 6 items')
        self.assertEqual(len(stats), 6)

    def _read_file(self, fname):
        from ncclient.xml_ import NCElement

        fpath = os.path.join(os.path.dirname(__file__),
                             'rpc-reply', fname)
        foo = open(fpath).read()
        rpc_reply = NCElement(foo, self.dev._conn.
                              _device_handler.transform_reply())\
            ._NCElement__doc
        return rpc_reply

    def _mock_manager(self, *args, **kwargs):
        if kwargs:
            device_params = kwargs['device_params']
            device_handler = make_device_handler(device_params)
            session = SSHSession(device_handler)
            return Manager(session, device_handler)

        if args:
            if args[0].tag == 'request-pfe-execute':
                file_name = (args[0].findtext('command')).replace(' ', '_')
                return self._read_file(file_name + '.xml')
