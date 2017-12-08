__author__ = "Nitin Kumar"
__credits__ = "Jeremy Schulman"

import unittest
import os
from nose.plugins.attrib import attr

from jnpr.junos import Device

from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession
from mock import MagicMock, patch
import yamlordereddictloader
from jnpr.junos.factory.factory_loader import FactoryLoader
import yaml


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

    @patch('jnpr.junos.Device.execute')
    def test_unstructured_mtip_cge_regex(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        from jnpr.junos.command.mtip_cge import MtipCgeSummaryTable
        stats = MtipCgeSummaryTable(self.dev)
        stats = stats.get()
        self.assertEqual(dict(stats), {2: {'fpc': 1,
                                           'id': 2,
                                           'ifd': 'et-1/0/0',
                                           'name': 'mtip_cge.1.0.0',
                                           'pic': 0,
                                           'ptr': '4f119fb8'},
                                       4: {'fpc': 1,
                                           'id': 4,
                                           'ifd': 'et-1/2/0',
                                           'name': 'mtip_cge.1.2.0',
                                           'pic': 2,
                                           'ptr': '4f119c98'},
                                       5: {'fpc': 1,
                                           'id': 5,
                                           'ifd': 'et-1/2/1',
                                           'name': 'mtip_cge.1.2.1',
                                           'pic': 2,
                                           'ptr': '4f119bf8'}})

    @patch('jnpr.junos.Device.execute')
    def test_unstructured_icmpstats_nested(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        from jnpr.junos.command.icmpstats import ICMPStatsTable
        stats = ICMPStatsTable(self.dev)
        stats = stats.get()
        self.assertEqual(dict(stats), {'discards': {'ICMP errors':
                                                    {'name': 'ICMP errors',
                                                        'value': 0},
                                                    'IP fragments': {'name': 'IP fragments', 'value': 0},
                                                    'bad dest addresses': {'name': 'bad dest addresses',
                                                                           'value': 0},
                                                    'bad source addresses': {'name': 'bad source addresses',
                                                                             'value': 0},
                                                    'multicasts': {'name': 'multicasts', 'value': 0},
                                                    'pps per iff': {'name': 'pps per iff', 'value': 500},
                                                    'pps total': {'name': 'pps total', 'value': 1000},
                                                    'throttled': {'name': 'throttled', 'value': 0},
                                                    'unknown originators': {'name': 'unknown originators',
                                                                            'value': 0}}, 'errors': {'ICMP errors':
                                                                                                     {'error': 0, 'name': 'ICMP errors'},
                                                                                                     'IP fragments': {'error': 0, 'name': 'IP fragments'},
                                                                                                     'bad cf mtu': {'error': 0, 'name': 'bad cf mtu'},
                                                                                                     'bad dest addresses': {'error': 0, 'name': 'bad dest addresses'},
                                                                                                     'bad input interface': {'error': 0,
                                                                                                                             'name': 'bad input interface'},
                                                                                                     'bad nh lookup': {'error': 0, 'name': 'bad nh lookup'},
                                                                                                     'bad route lookup': {'error': 0, 'name': 'bad route lookup'},
                                                                                                     'bad source addresses': {'error': 0,
                                                                                                                              'name': 'bad source addresses'},
                                                                                                     'invalid ICMP type': {'error': 0, 'name': 'invalid ICMP type'},
                                                                                                     'invalid protocol': {'error': 0, 'name': 'invalid protocol'},
                                                                                                     'multicasts': {'error': 0, 'name': 'multicasts'},
                                                                                                     'pps per iff': {'error': 500, 'name': 'pps per iff'},
                                                                                                     'pps total': {'error': 1000, 'name': 'pps total'},
                                                                                                     'runts': {'error': 0, 'name': 'runts'},
                                                                                                     'throttled': {'error': 0, 'name': 'throttled'},
                                                                                                     'unknown originators': {'error': 0,
                                                                                                                             'name': 'unknown originators'},
                                                                                                     'unknown unreachables': {'error': 0,
                                                                                                                              'name': 'unknown unreachables'},
                                                                                                     'unprocessed redirects': {'error': 0,
                                                                                                                               'name': 'unprocessed redirects'},
                                                                                                     'unsupported ICMP type': {'error': 0,
                                                                                                                               'name': 'unsupported ICMP type'}},
                                       'rate': {'pps per iff':
                                                {'name': 'pps per iff',
                                                 'rate': 500},
                                                'pps total': {'name': 'pps '
                                                              'total',
                                                              'rate': 1000}}})

    @patch('jnpr.junos.Device.execute')
    def test_unstructured_ithrottle_key_args(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        from jnpr.junos.command.ithrottle import IthrottleIDTable
        stats = IthrottleIDTable(self.dev).get()
        self.assertEqual(dict(stats), {'usg_enable': 1, 'min_usage': 25.0,
                                       'throttle_stats': {'Disables': 0,
                                                          'Starts': 65708652,
                                                          'AdjUp': 6, 'Stops': 65708652,
                                                          'AdjDown': 4, 'Enables': 0,
                                                          'Checks': 124149442},
                                       'max_usage': 50.0})

    @patch('jnpr.junos.Device.execute')
    def test_pci_errs_multi_key_regex(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        yaml_data = """
---
ShowPciErrorsTable:
  command: show pci errors {{ pci_controller_number }}
  target: fpc2
  args:
    pci_controller_number: 2
  key:
    - pci_addr
    - status_type

  view: ShowPciErrorsView

ShowPciErrorsView:
  regex:
    pci_addr: 'PCI ERROR: (\d+:\d+:\d+:\d+) \(0x[a-z0-9]+\)'
    status_type: '(Slot|Link) status :'
    status: '0x[a-z0-9]+'
  filters:
    - pci_addr
    - status
    """
        globals().update(FactoryLoader().load(yaml.load(yaml_data,
                                                        Loader=yamlordereddictloader.Loader)))
        stats = ShowPciErrorsTable(self.dev).get()
        self.assertEqual(dict(stats), {('2:2:9:0', 'Link'): {'status':
                                                             '0x00000001',
                                                             'pci_addr':
                                                                 '2:2:9:0'},
                                       ('2:2:9:0', 'Slot'): {'status':
                                                                 '0x0000004c',
                                                             'pci_addr':
                                                                 '2:2:9:0'}})

    @patch('jnpr.junos.Device.execute')
    def test_fpcmemory_multi_key_columns(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        yaml_data = """
---
FPCMemory:
    command: show memory
    target: fpc1
    key:
     - id
     - base
    view: FPCMemoryView

FPCMemoryView:
    columns:
        id: ID
        base: Base
        total: Total(b)
        free: Free(b)
        used: Used(b)
        perc: "%"
        name: Name
    filters:
      - total
      - free
      - id
      - base
        """
        globals().update(FactoryLoader().load(yaml.load(yaml_data,
                                                        Loader=yamlordereddictloader.Loader)))
        stats = FPCMemory(self.dev).get()
        self.assertEqual(dict(stats), {(2, 'bcdfffe0'):
                                       {'base': 'bcdfffe0', 'total': 52428784, 'id': 2,
                                        'free': 52428784}, (0, '4d9ad8e8'): {
            'base': '4d9ad8e8', 'total': 1726292636, 'id': 0, 'free':
                1514622708}, (1, 'b47ffb88'): {'base': 'b47ffb88', 'total':
                                               67108860, 'id': 1, 'free': 53057404}, (3, 'b87ffb88'): {'base':
                                                                                                       'b87ffb88', 'total': 73400316, 'id': 3, 'free': 73400316}})

    @patch('jnpr.junos.Device.execute')
    def test_item_regex_pq3_pci(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        from jnpr.junos.command.pq3pci import PQ3PCITable
        stats = PQ3PCITable(self.dev)
        stats = stats.get()
        self.assertEqual(dict(stats),
                         {'0:0:0:0': {'bdllp': 0, 'pci': '0:0:0:0', 'rto': 0,
                                      'rxe': 0},
                          '2:0:0:0': {'bdllp': 0, 'pci': '2:0:0:0', 'rto': 0,
                                      'rxe': 0},
                          '2:1:0:0': {'bdllp': 0, 'pci': '2:1:0:0', 'rto': 0,
                                      'rxe': 0},
                          '2:2:1:0': {'bdllp': 0, 'pci': '2:2:1:0', 'rto': 0,
                                      'rxe': 0},
                          '2:2:2:0': {'bdllp': 0, 'pci': '2:2:2:0', 'rto': 0,
                                      'rxe': 0},
                          '2:2:4:0': {'bdllp': 0, 'pci': '2:2:4:0', 'rto': 0,
                                      'rxe': 0},
                          '2:2:5:0': {'bdllp': 0, 'pci': '2:2:5:0', 'rto': 0,
                                      'rxe': 0},
                          '2:2:6:0': {'bdllp': 0, 'pci': '2:2:6:0', 'rto': 0,
                                      'rxe': 0},
                          '2:2:7:0': {'bdllp': 0, 'pci': '2:2:7:0', 'rto': 0,
                                      'rxe': 0},
                          '2:2:8:0': {'bdllp': 0, 'pci': '2:2:8:0', 'rto': 0,
                                      'rxe': 0},
                          '2:2:9:0': {'bdllp': 0, 'pci': '2:2:9:0', 'rto': 0,
                                      'rxe': 0}}
                         )

    @patch('jnpr.junos.Device.execute')
    def test_regex_with_fields(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        from jnpr.junos.command.schedulerinfo import SchedulerTable
        stats = SchedulerTable(self.dev)
        stats = stats.get()
        self.assertEqual(dict(stats), {'interrupt_time': 16786614, 'Idle': {
            'time_ms': 7397672498, 'cpu': '85%', 'name': 'Idle'}, 'Level 3':
            {'time_ms': 1, 'cpu': '0%', 'name': 'Level 3'}, 'thread': {'cpu':
                                                                       '4%', 'pid': 99, 'name': 'LU Background Service',
                                                                       'time': '410844018 ms'}})

    @patch('jnpr.junos.Device.execute')
    def test_exists(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        from jnpr.junos.command.host_lb_status import HostlbStatusSummaryTable
        stats = HostlbStatusSummaryTable(self.dev)
        stats = stats.get()
        self.assertEqual(dict(stats), {'no_detected_wedges': True,
                                       'no_toolkit_errors': True})

    @patch('jnpr.junos.Device.execute')
    def test_table_path_option(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        from jnpr.junos.command.host_lb_status import HostlbStatusSummaryTable
        stats = HostlbStatusSummaryTable(path=os.path.join(os.path.dirname(
            __file__), 'rpc-reply', 'show_host_loopback_status-summary.xml'))
        stats = stats.get()
        self.assertEqual(dict(stats), {'no_detected_wedges': True,
                                       'no_toolkit_errors': True})

    @patch('jnpr.junos.Device.execute')
    def test_title_without_view(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        from jnpr.junos.command.chassisethernetswitchstatistics import \
            EthernetSwitchStatistics
        stats = EthernetSwitchStatistics(self.dev)
        stats = stats.get()
        self.assertEqual(dict(stats),
                         {'fpc0': {},
                          'fpc1': {'RX Broadcast Packets': 9206817,
                                   'RX Byte Counter': 320925468,
                                   'RX Packets 1024-1518 Octets': 3200039,
                                   'RX Packets 512-1023 Octets': 4428661,
                                   'TX Packets 128-255 Octets': 6738243,
                                   'TX Packets 64 Octets': 142545489,
                                   'TX Packets 65-127 Octets': 83498558},
                          'fpc2': {'RX Byte Counter': 133138157,
                                   'RX Packets 1024-1518 Octets': 7994417,
                                   'RX Packets 128-255 Octets': 5848046,
                                   'RX Packets 256-511 Octets': 14518495,
                                   'RX Packets 512-1023 Octets': 33598800,
                                   'RX Packets 64 Octets': 69281885,
                                   'RX Packets 65-127 Octets': 98793558,
                                   'TX Broadcast Packets': 46011330,
                                   'TX Byte Counter': 12099160,
                                   'TX Packets 128-255 Octets': 11245893,
                                   'TX Packets 256-511 Octets': 55746,
                                   'TX Packets 512-1023 Octets': 3669,
                                   'TX Packets 64 Octets': 140666613,
                                   'TX Packets 65-127 Octets': 105545277},
                          'fpc3': {},
                          'fpc4': {'RX 1519-1522 Good Vlan frms': 0,
                                   'RX Align Errors': 0,
                                   'RX Broadcast Packets': 9216795,
                                   'RX Byte Counter': 361322476,
                                   'RX Control Frame Counter': 0,
                                   'RX FCS Errors': 0,
                                   'RX False Carrier Errors': 0,
                                   'RX Fragments': 0,
                                   'RX Jabbers': 0,
                                   'RX MTU Exceed Counter': 0,
                                   'RX Multicast Packets': 0,
                                   'RX Octets': 212488240,
                                   'RX Out of Range Length': 0,
                                   'RX Oversize Packets': 0,
                                   'RX Packets 1024-1518 Octets': 5524595,
                                   'RX Packets 128-255 Octets': 7153230,
                                   'RX Packets 1519-2047 Octets': 0,
                                   'RX Packets 2048-4095 Octets': 0,
                                   'RX Packets 256-511 Octets': 2130213,
                                   'RX Packets 4096-9216 Octets': 0,
                                   'RX Packets 512-1023 Octets': 24031621,
                                   'RX Packets 64 Octets': 69309261,
                                   'RX Packets 65-127 Octets': 104339320,
                                   'RX Pause Frame Counter': 0,
                                   'RX Symbol errors': 0,
                                   'RX Undersize Packets': 0,
                                   'RX Unsupported opcodes': 0,
                                   'TX 1519-1522 Good Vlan frms': 0,
                                   'TX Broadcast Packets': 45997099,
                                   'TX Byte Counter': 725771059,
                                   'TX Collision frames': 0,
                                   'TX Excessive Collisions': 0,
                                   'TX FCS Error Counter': 0,
                                   'TX Fragment Counter': 0,
                                   'TX Frame deferred Xmns': 0,
                                   'TX Frame excessive deferl': 0,
                                   'TX Jabbers': 0,
                                   'TX Late Collisions': 0,
                                   'TX MAC ctrl frames': 0,
                                   'TX Mult. Collision frames': 0,
                                   'TX Multicast Packets': 6,
                                   'TX Octets': 246717004,
                                   'TX Oversize Packets': 0,
                                   'TX PAUSEMAC Ctrl Frames': 0,
                                   'TX Packets 1024-1518 Octets': 72615,
                                   'TX Packets 128-255 Octets': 15940774,
                                   'TX Packets 1519-2047 Octets': 0,
                                   'TX Packets 2048-4095 Octets': 0,
                                   'TX Packets 256-511 Octets': 6737,
                                   'TX Packets 4096-9216 Octets': 0,
                                   'TX Packets 512-1023 Octets': 2934,
                                   'TX Packets 64 Octets': 1397543,
                                   'TX Packets 65-127 Octets': 91616401,
                                   'TX Single Collision frames': 0},
                          'fpc5': {}})


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
        if kwargs and 'normalize' not in kwargs:
            device_params = kwargs['device_params']
            device_handler = make_device_handler(device_params)
            session = SSHSession(device_handler)
            return Manager(session, device_handler)

        if args:
            if args[0].tag == 'request-pfe-execute':
                file_name = (args[0].findtext('command')).replace(' ', '_')
                return self._read_file(file_name + '.xml')
            elif args[0].tag == 'command':
                file_name = (args[0].text).replace(' ', '_')
                return self._read_file(file_name + '.xml')
