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
    def test_unstructured_cmerror(self, mock_execute):
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

    @patch('jnpr.junos.Device.execute')
    def test_unstructured_linkstats(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        from jnpr.junos.command.linkstats import FPCLinkStatTable
        stats = FPCLinkStatTable(self.dev)
        stats = stats.get()
        self.assertEqual(dict(stats),
                         {'PPP LCP/NCP': 0, 'ISIS': 0, 'BFD': 15, 'OAM': 0,
                          'ETHOAM': 0, 'LACP': 0, 'LMI': 0, 'UBFD': 0,
                          'HDLC keepalives': 0, 'OSPF Hello': 539156, 'RSVP':
                              0})

    @patch('jnpr.junos.Device.execute')
    def test_unstructured_ttpstatistics(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        from jnpr.junos.command.ttpstatistics import FPCTTPStatsTable
        stats = FPCTTPStatsTable(self.dev)
        stats = stats.get()
        self.assertEqual(dict(stats),
                         {'TTPQueueSizes': {'High': '0 (max is 4473)',
                                            'Low': '0 (max is 2236)'},
                          'TTPReceiveStatistics': {'Coalesce': {'control': 0,
                                                                'discard': 0,
                                                                'high': 0,
                                                                'low': 0,
                                                                'medium': 0,
                                                                'name':
                                                                'Coalesce'}},
                          'TTPStatistics': {
                              'Coalesce': {'name': 'Coalesce', 'rcvd': 0,
                                           'tras': 0},
                              'Coalesce Fail': {'name': 'Coalesce Fail',
                                                'rcvd': 0,
                                                'tras': 0},
                              'Drops': {'name': 'Drops', 'rcvd': 0, 'tras': 0},
                              'L2 Packets': {'name': 'L2 Packets',
                                             'rcvd': 4292,
                                             'tras': 1093544},
                              'L3 Packets': {'name': 'L3 Packets',
                                             'rcvd': 542638,
                                             'tras': 0},
                              'Netwk Fail': {'name': 'Netwk Fail', 'rcvd': 0,
                                             'tras': 0},
                              'Queue Drops': {'name': 'Queue Drops',
                                              'rcvd': 0,
                                              'tras': 0},
                              'Unknown': {'name': 'Unknown', 'rcvd': 0,
                                          'tras': 0}},
                          'TTPTransmitStatistics': {'L2 Packets': {'queue2': 0},
                                                    'L3 Packets': {
                                                        'queue2': 0}}})

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
