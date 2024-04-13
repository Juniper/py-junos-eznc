__author__ = "Nitin Kumar"
__credits__ = "Jeremy Schulman"

import unittest
import os
import nose2

from jnpr.junos import Device
from jnpr.junos.exception import RpcError

from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession
from mock import MagicMock, patch
import yamlordereddictloader
from jnpr.junos.factory.factory_loader import FactoryLoader
import yaml
import json


class TestFactoryCMDTable(unittest.TestCase):
    @patch("ncclient.manager.connect")
    def setUp(self, mock_connect):
        mock_connect.side_effect = self._mock_manager
        self.dev = Device(
            host="1.1.1.1", user="rick", password="password123", gather_facts=False
        )
        self.dev.open()

    @patch("jnpr.junos.Device.execute")
    def test_unstructured_cmerror(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        yaml_data = """
---
CMErrorTable:
  command: show cmerror module brief
  target: Null
  key:
    - module
  view: CMErrorView

CMErrorView:
  columns:
    module: Module
    name: Name
    errors: Active Errors
  filters:
    - errors
    - name
"""
        globals().update(
            FactoryLoader().load(
                yaml.load(yaml_data, Loader=yamlordereddictloader.Loader)
            )
        )
        stats = CMErrorTable(self.dev)
        stats = stats.get(target="fpc1")
        self.assertEqual(
            dict(stats),
            {
                1: {"errors": 0, "name": "PQ3 Chip"},
                2: {"errors": 0, "name": "Host Loopback"},
                3: {"errors": 0, "name": "CM[0]"},
                4: {"errors": 0, "name": "CM[1]"},
                5: {"errors": 0, "name": "LUCHIP(0)"},
                6: {"errors": 0, "name": "TOE-LU-0:0:0"},
            },
        )
        self.assertEqual(repr(stats), "CMErrorTable:1.1.1.1: 6 items")
        self.assertEqual(len(stats), 6)

    @patch("jnpr.junos.Device.execute")
    def test_unstructured_sysctl_oneline_op(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        yaml_data = """
---
sysctlVeriexecTable:
    command: request routing-engine execute command sysctl dummy
    view: sysctlView

sysctlView:
   regex:
        veriexec-name: '(.*):'
        veriexec-state: '(.*)'
"""
        globals().update(
            FactoryLoader().load(
                yaml.load(yaml_data, Loader=yamlordereddictloader.Loader)
            )
        )
        stats = sysctlVeriexecTable(self.dev)
        stats = stats.get()
        self.assertEqual(
            dict(stats),
            {
                "veriexec-name": "security.mac.veriexec.state",
                "veriexec-state": "loaded active enforce",
            },
        )
        self.assertEqual(repr(stats), "sysctlVeriexecTable:1.1.1.1: 2 items")
        self.assertEqual(len(stats), 2)

    @patch("jnpr.junos.Device.execute")
    def test_unstructured_cmerror_multiline_header(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        yaml_data = """
---
CMErrorTable:
  command: show cmerror module brief dummy multiline
  target: Null
  key: module
  view: CMErrorView

CMErrorView:
  columns:
    module: Module
    name: Name
    errors: Active Errors
    pfe:
      - PFE
      - Specific
    callback:
      - Callback
      - Function
    data: ModuleData
    """
        globals().update(
            FactoryLoader().load(
                yaml.load(yaml_data, Loader=yamlordereddictloader.Loader)
            )
        )
        stats = CMErrorTable(self.dev)
        stats = stats.get(target="fpc1")
        self.assertEqual(
            dict(stats),
            {
                1: {
                    "errors": 0,
                    "pfe": "Yes",
                    "name": "PQ3 Chip",
                    "module": 1,
                    "callback": "0x00000000",
                    "data": "0x00000000",
                },
                2: {
                    "errors": 0,
                    "pfe": "No",
                    "name": "Host Loopback",
                    "module": 2,
                    "callback": "0x00000000",
                    "data": "0x464295b0",
                },
                3: {
                    "errors": 0,
                    "pfe": "No",
                    "name": "CM[0]",
                    "module": 3,
                    "callback": "0x41f550f0",
                    "data": "0x462f767c",
                },
                4: {
                    "errors": 0,
                    "pfe": "No",
                    "name": "LUCHIP(0)",
                    "module": 4,
                    "callback": "0x00000000",
                    "data": "0x481b84d8",
                },
            },
        )
        self.assertEqual(repr(stats), "CMErrorTable:1.1.1.1: 4 items")
        self.assertEqual(len(stats), 4)

    def test_view_variable(self):
        yaml_data = """
---
CMErrorTable:
  command: show cmerror module brief
  target: Null
  key: module
  view: CMErrorView

CMErrorView:
  columns:
    module: Module
    name: Name
    errors: Active Errors
"""
        globals().update(
            FactoryLoader().load(
                yaml.load(yaml_data, Loader=yamlordereddictloader.Loader)
            )
        )
        stats = CMErrorTable(self.dev)
        stats.view = globals()["CMErrorView"]
        self.assertEqual(stats.view, globals()["CMErrorView"])

    def test_view_setter_raise_exception(self):
        yaml_data = """
---
CMErrorTable:
  command: show cmerror module brief
  target: Null
  key: module
  view: CMErrorView

CMErrorView:
  columns:
    module: Module
    name: Name
    errors: Active Errors
"""
        globals().update(
            FactoryLoader().load(
                yaml.load(yaml_data, Loader=yamlordereddictloader.Loader)
            )
        )
        stats = CMErrorTable(self.dev)

        with self.assertRaises(ValueError):
            stats.view = "dummy"

    @patch("paramiko.SSHClient")
    @patch("jnpr.junos.utils.start_shell.StartShell.wait_for")
    @patch("jnpr.junos.Device.execute")
    def test_request_pfe_rpc_not_avialable(self, mock_execute, mock_ss, mock_ssh_conn):
        mock_execute.side_effect = RpcError(rsp="ok")
        yaml_data = """
---
CMErrorTable:
  command: show cmerror module brief
  target: fpc1
  key: module
  view: CMErrorView

CMErrorView:
  columns:
    module: Module
    name: Name
"""
        globals().update(
            FactoryLoader().load(
                yaml.load(yaml_data, Loader=yamlordereddictloader.Loader)
            )
        )
        stats = CMErrorTable(self.dev)
        with patch("jnpr.junos.utils.start_shell.StartShell.run") as ss_run:
            stats.get()
        ss_run.assert_called_with('cprod -A fpc1 -c "show cmerror module brief"')

    @patch("jnpr.junos.Device.execute")
    def test_get_api_params(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        yaml_data = """
---
CMErrorTable:
    command: show cmerror module brief
    target: fpc1
    key: name
    view: CMErrorView

CMErrorView:
    columns:
        module: Module
        name: Name
        errors: Active Errors
    """
        globals().update(
            FactoryLoader().load(
                yaml.load(yaml_data, Loader=yamlordereddictloader.Loader)
            )
        )
        stats = CMErrorTable(self.dev)
        stats.get(key="module", key_items=[1], filters=["errors"])
        self.assertEqual(dict(stats), {1: {"errors": 0}})

    @patch("jnpr.junos.Device.execute")
    def test_cmdview_properties(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        yaml_data = """
---
CMErrorTable:
    command: show cmerror module brief
    target: fpc1
    key: name
    view: CMErrorView

CMErrorView:
    columns:
        module: Module
        name: Name
        errors: Active Errors
"""
        globals().update(
            FactoryLoader().load(
                yaml.load(yaml_data, Loader=yamlordereddictloader.Loader)
            )
        )
        stats = CMErrorTable(self.dev).get()
        self.assertEqual(stats.VIEW.T.__class__.__name__, "property")
        self.assertEqual(stats.VIEW.xml.__class__.__name__, "property")
        expected = [
            "Host Loopback",
            "CM[1]",
            "CM[0]",
            "LUCHIP(0)",
            "TOE-LU-0:0:0",
            "PQ3 Chip",
        ]
        expected.sort()
        got_keys = list(stats.keys())
        got_keys.sort()
        self.assertListEqual(got_keys, expected)
        got_values = list(stats.values())
        got_items = list(stats.items())
        self.assertEqual(repr(stats), "CMErrorTable:1.1.1.1: 6 items")

    @patch("jnpr.junos.Device.execute")
    def test_cmdtable_iter(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        yaml_data = """
---
FPCLinkStatTable:
  command: show link stats
  target: Null
  delimiter: ":"
"""
        globals().update(
            FactoryLoader().load(
                yaml.load(yaml_data, Loader=yamlordereddictloader.Loader)
            )
        )
        stats = FPCLinkStatTable(self.dev)
        stats = stats.get(target="fpc1")
        self.assertEqual(
            {k: v for k, v in stats},
            {
                "PPP LCP/NCP": 0,
                "ISIS": 0,
                "BFD": 15,
                "OAM": 0,
                "ETHOAM": 0,
                "LACP": 0,
                "LMI": 0,
                "UBFD": 0,
                "HDLC keepalives": 0,
                "OSPF Hello": 539156,
                "RSVP": 0,
            },
        )

    @patch("jnpr.junos.Device.execute")
    def test_title_in_view(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        yaml_data = """
---
ShowLuchipTable:
  command: show luchip {{ lu_instance }}
  target: Null
  args:
    lu_instance: 0
  key: ppe
  view: ShowLuchipView

ShowLuchipView:
  title: PPE Zone Enable masks and (active)
  regex:
    ppe: 'PPE\[(\d+)\]'
    zone_enable_mask: 'Zone Enable Mask (0x[a-z0-9]+)'
    active_zones: '\((0x[a-z0-9]+)\)'
"""
        globals().update(
            FactoryLoader().load(
                yaml.load(yaml_data, Loader=yamlordereddictloader.Loader)
            )
        )
        stats = ShowLuchipTable(self.dev)
        stats = stats.get(target="fpc1")
        self.assertEqual(
            dict(stats),
            {
                0: {
                    "active_zones": "0x00000000",
                    "ppe": 0,
                    "zone_enable_mask": "0xfcff0ffe",
                },
                1: {
                    "active_zones": "0x00000000",
                    "ppe": 1,
                    "zone_enable_mask": "0xfcff0fff",
                },
                2: {
                    "active_zones": "0x00000000",
                    "ppe": 2,
                    "zone_enable_mask": "0xfcff0fff",
                },
                3: {
                    "active_zones": "0x00000000",
                    "ppe": 3,
                    "zone_enable_mask": "0xfcff0fff",
                },
                4: {
                    "active_zones": "0x00000000",
                    "ppe": 4,
                    "zone_enable_mask": "0xfcff0fff",
                },
                5: {
                    "active_zones": "0x00000000",
                    "ppe": 5,
                    "zone_enable_mask": "0xfcff0fff",
                },
                6: {
                    "active_zones": "0x00000000",
                    "ppe": 6,
                    "zone_enable_mask": "0xfcff0fff",
                },
                7: {
                    "active_zones": "0x00000000",
                    "ppe": 7,
                    "zone_enable_mask": "0xfcff0fff",
                },
                8: {
                    "active_zones": "0x00000000",
                    "ppe": 8,
                    "zone_enable_mask": "0xfcff0fff",
                },
                9: {
                    "active_zones": "0x00000000",
                    "ppe": 9,
                    "zone_enable_mask": "0xfcff0fff",
                },
                10: {
                    "active_zones": "0x00000100",
                    "ppe": 10,
                    "zone_enable_mask": "0xfcff0fff",
                },
                11: {
                    "active_zones": "0x00000000",
                    "ppe": 11,
                    "zone_enable_mask": "0xfcff0fff",
                },
                12: {
                    "active_zones": "0x00000000",
                    "ppe": 12,
                    "zone_enable_mask": "0xfcff0fff",
                },
                13: {
                    "active_zones": "0x00000000",
                    "ppe": 13,
                    "zone_enable_mask": "0xfcff0fff",
                },
                14: {
                    "active_zones": "0x00000000",
                    "ppe": 14,
                    "zone_enable_mask": "0xfcff0fff",
                },
                15: {
                    "active_zones": "0x00000000",
                    "ppe": 15,
                    "zone_enable_mask": "0xfcff0fff",
                },
            },
        )

    @patch("jnpr.junos.Device.execute")
    def test_unstructured_linkstats(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        yaml_data = """
---
FPCLinkStatTable:
    command: show link stats
    target: Null
    delimiter: ":"
"""
        globals().update(
            FactoryLoader().load(
                yaml.load(yaml_data, Loader=yamlordereddictloader.Loader)
            )
        )
        stats = FPCLinkStatTable(self.dev)
        stats = stats.get(target="fpc1")
        self.assertEqual(
            dict(stats),
            {
                "PPP LCP/NCP": 0,
                "ISIS": 0,
                "BFD": 15,
                "OAM": 0,
                "ETHOAM": 0,
                "LACP": 0,
                "LMI": 0,
                "UBFD": 0,
                "HDLC keepalives": 0,
                "OSPF Hello": 539156,
                "RSVP": 0,
            },
        )

    @patch("jnpr.junos.Device.execute")
    def test_field_eval(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        yaml_data = """
---
XMChipStatsTable:
  command: show xmchip {{ instance }} pt stats
  args:
    instance: -1
  target: fpc2
  item: '*'
  view: XMChipStatsView

XMChipStatsView:
  regex:
    pct_wi_1: 'PCT entries used by all WI-1 streams\s+:\s?(\d+)'
    pct_wi_0: 'PCT entries used by all WI-0 streams\s+:\s?(\d+)'
  eval:
    total_pct: '{{ pct_wi_1 }} + {{ pct_wi_0 }}'
"""
        globals().update(
            FactoryLoader().load(
                yaml.load(yaml_data, Loader=yamlordereddictloader.Loader)
            )
        )
        stats = XMChipStatsTable(self.dev)
        stats = stats.get(target="fpc1", args={"instance": 0})
        self.assertEqual(dict(stats), {"pct_wi_1": 0, "pct_wi_0": 0, "total_pct": 0})

    @patch("jnpr.junos.Device.execute")
    def test__contains__(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        yaml_data = """
---
FPCLinkStatTable:
    command: show link stats
    target: Null
    delimiter: ":"
"""
        globals().update(
            FactoryLoader().load(
                yaml.load(yaml_data, Loader=yamlordereddictloader.Loader)
            )
        )
        stats = FPCLinkStatTable(self.dev)
        stats = stats.get(target="fpc1")
        self.assertTrue("OSPF Hello" in stats)

    @patch("jnpr.junos.Device.execute")
    def test_unstructured_ttpstatistics(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        yaml_data = """
---
FPCTTPStatsTable:
  command: show ttp statistics
  target: Null
  view: FPCTTPStatsView

FPCTTPStatsView:
  fields:
    TTPStatistics: _FPCTTPStatisticsTable
    TTPTransmitStatistics: _FPCTTPTransmitStatisticsTable
    TTPReceiveStatistics: _FPCTTPReceiveStatisticsTable
    TTPQueueSizes: _FPCTTPQueueSizesTable
    TTPQueueSizes2: _FPCTTPQueueSizesTable2

_FPCTTPStatisticsTable:
  title: TTP Statistics
  view: _FPCTTPStatisticsView

_FPCTTPStatisticsView:
  columns:
    rcvd: Receive
    tras: Transmit

_FPCTTPTransmitStatisticsTable:
  title: TTP Transmit Statistics
  view: _FPCTTPTransmitStatisticsView

_FPCTTPTransmitStatisticsView:
  columns:
    queue0: Queue 0
    queue1: Queue 1
    queue2: Queue 2
    queue3: Queue 3
  filters:
    - queue2

_FPCTTPReceiveStatisticsTable:
  title: TTP Receive Statistics
  key: name
  key_items:
    - Coalesce
  view: _FPCTTPReceiveStatisticsView

_FPCTTPReceiveStatisticsView:
  columns:
    control: Control
    high: High
    medium: Medium
    low: Low
    discard: Discard

_FPCTTPQueueSizesTable:
  title: TTP Receive Queue Sizes
  delimiter: ":"
  key_items:
    - High
    - Low
  # view: _FPCTTPQueueSizesView

_FPCTTPQueueSizesTable2:
  title: TTP Receive Queue Sizes
  delimiter: ":"
  key_items:
    - High
    - Low
  # view: _FPCTTPQueueSizesView

_FPCTTPQueueSizesView:
  fields:
    high: High

TTPReceiveStatsTable:
  command: show ttp statistics
  target: Null
  title: TTP Receive Statistics
  key: name
  view: FPCTTPReceiveStatsView

FPCTTPReceiveStatsView:
  columns:
    control: Control
    high: High
    medium: Medium
    low: Low
    discard: Discard
"""
        globals().update(
            FactoryLoader().load(
                yaml.load(yaml_data, Loader=yamlordereddictloader.Loader)
            )
        )
        stats = FPCTTPStatsTable(self.dev)
        stats = stats.get(target="fpc2")
        self.assertEqual(
            dict(stats),
            {
                "TTPQueueSizes": {"High": "0 (max is 4473)", "Low": "0 (max is 2236)"},
                "TTPQueueSizes2": {"High": "0 (max is 4473)", "Low": "0 (max is 2236)"},
                "TTPReceiveStatistics": {
                    "Coalesce": {
                        "control": 0,
                        "discard": 0,
                        "high": 0,
                        "low": 0,
                        "medium": 0,
                        "name": "Coalesce",
                    }
                },
                "TTPStatistics": {
                    "Coalesce": {"name": "Coalesce", "rcvd": 0, "tras": 0},
                    "Coalesce Fail": {"name": "Coalesce Fail", "rcvd": 0, "tras": 0},
                    "Drops": {"name": "Drops", "rcvd": 0, "tras": 0},
                    "L2 Packets": {"name": "L2 Packets", "rcvd": 4292, "tras": 1093544},
                    "L3 Packets": {"name": "L3 Packets", "rcvd": 542638, "tras": 0},
                    "Netwk Fail": {"name": "Netwk Fail", "rcvd": 0, "tras": 0},
                    "Queue Drops": {"name": "Queue Drops", "rcvd": 0, "tras": 0},
                    "Unknown": {"name": "Unknown", "rcvd": 0, "tras": 0},
                },
                "TTPTransmitStatistics": {
                    "L2 Packets": {"queue2": 0},
                    "L3 Packets": {"queue2": 0},
                },
            },
        )

    @patch("jnpr.junos.Device.execute")
    def test_unstructured_mtip_cge_regex(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        yaml_data = """
---
MtipCgeSummaryTable:
  command: show mtip-cge summary
  target: Null
  key: id
  view: MtipCgeSummaryView

MtipCgeSummaryView:
  regex:
    id: numbers
    name: "[a-z0-9_.]+"
    fpc: numbers
    pic: numbers
    ifd: '(\w+-\d(/\d){2})'
    ptr: "[a-f0-9]+"

MtipCgeStatisticsTable:
  command: show mtip-cge {{ mtip_id }} statistics
  args:
    mtip_id: 11
  target: Null
  delimiter: ":"
  title: Statistics
  key_items:
    - aFrameCheckSequenceErrors
    - aAlignmentErrors
    - aPAUSEMACCtrlFramesTransmitted
    - aPAUSEMACCtrlFramesReceived
    - aFrameTooLongErrors
    - aInRangeLengthErrors
"""
        globals().update(
            FactoryLoader().load(
                yaml.load(yaml_data, Loader=yamlordereddictloader.Loader)
            )
        )
        stats = MtipCgeSummaryTable(self.dev)
        stats = stats.get(target="fpc2")
        self.assertEqual(
            dict(stats),
            {
                2: {
                    "fpc": 1,
                    "id": 2,
                    "ifd": "et-1/0/0",
                    "name": "mtip_cge.1.0.0",
                    "pic": 0,
                    "ptr": "4f119fb8",
                },
                4: {
                    "fpc": 1,
                    "id": 4,
                    "ifd": "et-1/2/0",
                    "name": "mtip_cge.1.2.0",
                    "pic": 2,
                    "ptr": "4f119c98",
                },
                5: {
                    "fpc": 1,
                    "id": 5,
                    "ifd": "et-1/2/1",
                    "name": "mtip_cge.1.2.1",
                    "pic": 2,
                    "ptr": "4f119bf8",
                },
            },
        )

    @patch("jnpr.junos.Device.execute")
    def test_unstructured_icmpstats_nested(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        yaml_data = """
---
ICMPStatsTable:
  command: show icmp statistics
  target: Null
  view: ICMPStatsView

ICMPStatsView:
  fields:
    statistics: _ICMPStatisticsTable
    discards: _ICMPDiscardsTable
    errors: _ICMPErrorsTable
    rate: _ICMPRateTable

_ICMPStatisticsTable:
  title: ICMP Statistics
  key: name
  view: _ICMPStatisticsView

_ICMPStatisticsView:
  regex:
    value: numbers
    name: words

_ICMPDiscardsTable:
  title: ICMP Discards
  key: name
  view: _ICMPDiscardsView

_ICMPDiscardsView:
  regex:
    value: numbers
    name: words

_ICMPErrorsTable:
  title: ICMP Errors
  key: name
  view: _ICMPErrorsView

_ICMPErrorsView:
  regex:
    error: numbers
    name: words

_ICMPRateTable:
  title: ICMP Rate Limit Settings
  key: name
  view: _ICMPRateView

_ICMPRateView:
  regex:
    rate: numbers
    name: words
"""
        globals().update(
            FactoryLoader().load(
                yaml.load(yaml_data, Loader=yamlordereddictloader.Loader)
            )
        )
        stats = ICMPStatsTable(self.dev)
        stats = stats.get(target="fpc2")
        self.assertEqual(
            dict(stats),
            {
                "discards": {
                    "bad source addresses": {
                        "name": "bad source addresses",
                        "value": 0,
                    },
                    "unknown originators": {"name": "unknown originators", "value": 0},
                    "bad dest addresses": {"name": "bad dest addresses", "value": 0},
                    "multicasts": {"name": "multicasts", "value": 0},
                    "IP fragments": {"name": "IP fragments", "value": 0},
                    "ICMP errors": {"name": "ICMP errors", "value": 0},
                },
                "rate": {
                    "pps total": {"rate": 1000, "name": "pps total"},
                    "pps per iff": {"rate": 500, "name": "pps per iff"},
                },
                "statistics": {
                    "other unreachables": {"name": "other unreachables", "value": 0},
                    "redirects": {"name": "redirects", "value": 0},
                    "igmp v1 handoffs": {"name": "igmp v1 handoffs", "value": 0},
                    "parameter problems": {"name": "parameter problems", "value": 0},
                    "throttled": {"name": "throttled", "value": 0},
                    "tag te requests": {"name": "tag te requests", "value": 0},
                    "network unreachables": {
                        "name": "network unreachables",
                        "value": 0,
                    },
                    "source route denials": {
                        "name": "source route denials",
                        "value": 0,
                    },
                    "filter prohibited": {"name": "filter prohibited", "value": 0},
                    "ttl captured": {"name": "ttl captured", "value": 0},
                    "mtu exceeded": {"name": "mtu exceeded", "value": 0},
                    "requests": {"name": "requests", "value": 0},
                    "icmp": {"name": "icmp", "value": 0},
                    "ttl expired": {"name": "ttl expired", "value": 0},
                    "tag te to RE": {"name": "tag te to RE", "value": 0},
                },
                "errors": {
                    "bad nh lookup": {"name": "bad nh lookup", "error": 0},
                    "invalid ICMP type": {"name": "invalid ICMP type", "error": 0},
                    "unprocessed redirects": {
                        "name": "unprocessed redirects",
                        "error": 0,
                    },
                    "bad cf mtu": {"name": "bad cf mtu", "error": 0},
                    "bad route lookup": {"name": "bad route lookup", "error": 0},
                    "invalid protocol": {"name": "invalid protocol", "error": 0},
                    "runts": {"name": "runts", "error": 0},
                    "bad input interface": {"name": "bad input interface", "error": 0},
                    "unsupported ICMP type": {
                        "name": "unsupported ICMP type",
                        "error": 0,
                    },
                    "unknown unreachables": {
                        "name": "unknown unreachables",
                        "error": 0,
                    },
                },
            },
        )
        self.assertTrue(stats.D.__class__.__name__ == "Device")

    @patch("jnpr.junos.Device.execute")
    def test_unstructured_ithrottle_key_args(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        yaml_data = """
IthrottleIDTable:
  command: show ithrottle id {{ id }}
  args:
    id: 0
  item: '*'
  target: Null
  view: IthrottleIDView

IthrottleIDView:
  regex:
    min_usage: 'Min Usage Perc:    (\d+\.\d+)'
    max_usage: 'Max Usage Perc:    (\d+\.\d+)'
    usg_enable: 'AdjustUsageEnable: (\d)'
  fields:
    throttle_stats: _ThrottleStatsTable

_ThrottleStatsTable:
    title: Throttle Stats
    delimiter: ":"
    key_items:
      - Disables
      - AdjDown
      - Enables
"""
        globals().update(
            FactoryLoader().load(
                yaml.load(yaml_data, Loader=yamlordereddictloader.Loader)
            )
        )
        stats = IthrottleIDTable(self.dev).get(target="fpc2")
        self.assertEqual(
            dict(stats),
            {
                "usg_enable": 1,
                "min_usage": 25.0,
                "throttle_stats": {"Disables": 0, "AdjDown": 4, "Enables": 0},
                "max_usage": 50.0,
            },
        )

    @patch("jnpr.junos.Device.execute")
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
        globals().update(
            FactoryLoader().load(
                yaml.load(yaml_data, Loader=yamlordereddictloader.Loader)
            )
        )
        stats = ShowPciErrorsTable(self.dev).get()
        self.assertEqual(
            dict(stats),
            {
                ("2:2:9:0", "Link"): {"status": "0x00000001", "pci_addr": "2:2:9:0"},
                ("2:2:9:0", "Slot"): {"status": "0x0000004c", "pci_addr": "2:2:9:0"},
            },
        )

    @patch("jnpr.junos.Device.execute")
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
        globals().update(
            FactoryLoader().load(
                yaml.load(yaml_data, Loader=yamlordereddictloader.Loader)
            )
        )
        stats = FPCMemory(self.dev).get()
        self.assertEqual(
            dict(stats),
            {
                (2, "bcdfffe0"): {
                    "base": "bcdfffe0",
                    "total": 52428784,
                    "id": 2,
                    "free": 52428784,
                },
                (0, "4d9ad8e8"): {
                    "base": "4d9ad8e8",
                    "total": 1726292636,
                    "id": 0,
                    "free": 1514622708,
                },
                (1, "b47ffb88"): {
                    "base": "b47ffb88",
                    "total": 67108860,
                    "id": 1,
                    "free": 53057404,
                },
                (3, "b87ffb88"): {
                    "base": "b87ffb88",
                    "total": 73400316,
                    "id": 3,
                    "free": 73400316,
                },
            },
        )

    @patch("jnpr.junos.Device.execute")
    def test_item_regex_pq3_pci(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        yaml_data = """
---
PQ3PCITable:
  command: show pq3 pci
  target: Null
  item: PCI
  key:
    - pci
  view: PQ3PCI

PQ3PCI:
  regex:
    pci: 'PCI (\d+(:\d+){3})'
    rto: 'rto (\d+)'
    rnr: 'rnr (\d+)'
    rxe: 'rxe (\d+)'
    bdllp: 'bdllp (\d+)'
    btlp: 'btlp (\d+)'
"""
        globals().update(
            FactoryLoader().load(
                yaml.load(yaml_data, Loader=yamlordereddictloader.Loader)
            )
        )
        stats = PQ3PCITable(self.dev)
        stats = stats.get(target="fpc2")
        self.assertEqual(
            dict(stats),
            {
                "0:0:0:0": {
                    "bdllp": 0,
                    "btlp": 0,
                    "pci": "0:0:0:0",
                    "rnr": 0,
                    "rto": 0,
                    "rxe": 0,
                },
                "2:0:0:0": {
                    "bdllp": 0,
                    "btlp": 0,
                    "pci": "2:0:0:0",
                    "rnr": 0,
                    "rto": 0,
                    "rxe": 0,
                },
                "2:1:0:0": {
                    "bdllp": 0,
                    "btlp": 0,
                    "pci": "2:1:0:0",
                    "rnr": 0,
                    "rto": 0,
                    "rxe": 0,
                },
                "2:2:1:0": {
                    "bdllp": 0,
                    "btlp": 0,
                    "pci": "2:2:1:0",
                    "rnr": 0,
                    "rto": 0,
                    "rxe": 0,
                },
                "2:2:2:0": {
                    "bdllp": 0,
                    "btlp": 0,
                    "pci": "2:2:2:0",
                    "rnr": 0,
                    "rto": 0,
                    "rxe": 0,
                },
                "2:2:4:0": {
                    "bdllp": 0,
                    "btlp": 0,
                    "pci": "2:2:4:0",
                    "rnr": 0,
                    "rto": 0,
                    "rxe": 0,
                },
                "2:2:5:0": {
                    "bdllp": 0,
                    "btlp": 0,
                    "pci": "2:2:5:0",
                    "rnr": 0,
                    "rto": 0,
                    "rxe": 0,
                },
                "2:2:6:0": {
                    "bdllp": 0,
                    "btlp": 0,
                    "pci": "2:2:6:0",
                    "rnr": 0,
                    "rto": 0,
                    "rxe": 0,
                },
                "2:2:7:0": {
                    "bdllp": 0,
                    "btlp": 0,
                    "pci": "2:2:7:0",
                    "rnr": 0,
                    "rto": 0,
                    "rxe": 0,
                },
                "2:2:8:0": {
                    "bdllp": 0,
                    "btlp": 0,
                    "pci": "2:2:8:0",
                    "rnr": 0,
                    "rto": 0,
                    "rxe": 0,
                },
                "2:2:9:0": {
                    "bdllp": 0,
                    "btlp": 0,
                    "pci": "2:2:9:0",
                    "rnr": 0,
                    "rto": 0,
                    "rxe": 0,
                },
            },
        )

    @patch("jnpr.junos.Device.execute")
    def test_regex_with_fields(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        yaml_data = """
---
SchedulerTable:
  command: show sched
  target: Null
  key: name
  view: SchedulerView

SchedulerView:
  fields:
    thread: _TopThreadTable
  columns:
    cpu: CPU
    name: Name
    time_ms: Time(ms)
  regex:
    interrupt_time: 'Total interrupt time (\d+)'

_TopThreadTable:
  title: Top Thread
  delimiter: "="
"""
        globals().update(
            FactoryLoader().load(
                yaml.load(yaml_data, Loader=yamlordereddictloader.Loader)
            )
        )
        stats = SchedulerTable(self.dev)
        stats = stats.get(target="fpc1")
        self.assertEqual(
            dict(stats),
            {
                "interrupt_time": 16786614,
                "Idle": {"time_ms": 7397672498, "cpu": "85%", "name": "Idle"},
                "Level 3": {"time_ms": 1, "cpu": "0%", "name": "Level 3"},
                "thread": {
                    "cpu": "4%",
                    "pid": 99,
                    "name": "LU Background Service",
                    "time": "410844018 ms",
                },
            },
        )

    @patch("jnpr.junos.Device.execute")
    def test_exists(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        yaml_data = """
---
HostlbStatusSummaryTable:
  command: show host_loopback status-summary
  target: Null
  view: HostlbStatusSummaryView

HostlbStatusSummaryView:
  exists:
    no_detected_wedges: No detected wedges
    no_toolkit_errors: No toolkit errors
"""
        globals().update(
            FactoryLoader().load(
                yaml.load(yaml_data, Loader=yamlordereddictloader.Loader)
            )
        )
        stats = HostlbStatusSummaryTable(self.dev)
        stats = stats.get(target="fpc3")
        self.assertEqual(
            dict(stats), {"no_detected_wedges": True, "no_toolkit_errors": True}
        )

    @patch("jnpr.junos.Device.execute")
    def test_table_path_option(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        yaml_data = """
---
HostlbStatusSummaryTable:
  command: show host_loopback status-summary
  target: Null
  view: HostlbStatusSummaryView

HostlbStatusSummaryView:
  exists:
    no_detected_wedges: No detected wedges
    no_toolkit_errors: No toolkit errors
"""
        globals().update(
            FactoryLoader().load(
                yaml.load(yaml_data, Loader=yamlordereddictloader.Loader)
            )
        )
        stats = HostlbStatusSummaryTable(
            path=os.path.join(
                os.path.dirname(__file__),
                "rpc-reply",
                "show_host_loopback_status-summary.xml",
            )
        )
        stats = stats.get()
        self.assertEqual(
            dict(stats), {"no_detected_wedges": True, "no_toolkit_errors": True}
        )

    @patch("jnpr.junos.Device.execute")
    def test_table_with_item_regex(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        yaml_data = """
---
DevicesLocalTable:
  command: show devices local
  target: Null
  item: 'TSEC Ethernet Device Driver: (\.?\w+),'
  key: name
  view: DevicesLocalView

DevicesLocalView:
  fields:
    TSEC_status_counters: _TSECStatusCountersTable
    receive_counters: _ReceiveTable
    transmit_per_queue: _TransmitQueueTable

_ReceiveTable:
  item: '*'
  title: 'Receive:'
  view: _ReceiveView

_ReceiveView:
  regex:
    bytes: '(\d+) bytes'
    packets: '(\d+) packets'
    FCS_errors: '(\d+) FCS errors'
    broadcast_packets: '(\d+) broadcast packets'

_TSECStatusCountersTable:
  item: '*'
  title: 'TSEC status counters:'
  view: _TSECStatusCountersView

_TSECStatusCountersView:
  regex:
    kernel_dropped: 'kernel_dropped:(\d+)'
    rx_large: 'rx_large:(\d+)'

_TransmitQueueTable:
  item: '\[(\d+)\]'
  title: 'Transmit per queue:'
  view: _TransmitQueueView

_TransmitQueueView:
  fields:
    queue: _TransmitPerQueueTable

_TransmitPerQueueTable:
  title: 'Transmit per queue:'
  item: '*'
  view: _TransmitPerQueueView

_TransmitPerQueueView:
  regex:
    bytes: '(\d+) bytes'
    packets: '(\d+) packets'
"""
        globals().update(
            FactoryLoader().load(
                yaml.load(yaml_data, Loader=yamlordereddictloader.Loader)
            )
        )
        stats = DevicesLocalTable(self.dev)
        stats = stats.get(target="fpc1")
        self.assertEqual(
            dict(stats),
            {
                ".le1": {
                    "TSEC_status_counters": {"kernel_dropped": 0, "rx_large": 0},
                    "receive_counters": {
                        "FCS_errors": 0,
                        "broadcast_packets": 107271,
                        "bytes": 185584608,
                        "packets": 2250212,
                    },
                    "transmit_per_queue": {
                        0: {"queue": {"bytes": 10300254, "packets": 72537}},
                        1: {"queue": {"bytes": 4474302, "packets": 106531}},
                        2: {"queue": {"bytes": 260203538, "packets": 1857137}},
                        3: {"queue": {"bytes": 199334, "packets": 2179}},
                    },
                },
                ".le3": {
                    "TSEC_status_counters": {"kernel_dropped": 0, "rx_large": 0},
                    "receive_counters": {
                        "FCS_errors": 0,
                        "broadcast_packets": 0,
                        "bytes": 0,
                        "packets": 0,
                    },
                    "transmit_per_queue": {
                        0: {"queue": {"bytes": 0, "packets": 0}},
                        1: {"queue": {"bytes": 4474302, "packets": 106531}},
                        2: {"queue": {"bytes": 0, "packets": 0}},
                        3: {"queue": {"bytes": 0, "packets": 0}},
                    },
                },
            },
        )

    @patch("jnpr.junos.Device.execute")
    def test_table_item_group_key_mismatch(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        yaml_data = """
---
DevicesLocalTable:
  command: show devices local
  target: fpc1
  item: '(TSEC) Ethernet Device Driver: (\.?\w+),'
  key: name
  view: DevicesLocalView

DevicesLocalView:
  fields:
    receive_counters: _ReceiveTable

_ReceiveTable:
  item: '*'
  title: 'Receive:'
  view: _ReceiveView

_ReceiveView:
  regex:
    bytes: '(\d+) bytes'
    packets: '(\d+) packets'
    FCS_errors: '(\d+) FCS errors'
    broadcast_packets: '(\d+) broadcast packets'
"""
        globals().update(
            FactoryLoader().load(
                yaml.load(yaml_data, Loader=yamlordereddictloader.Loader)
            )
        )
        stats = DevicesLocalTable(self.dev)
        self.assertRaises(KeyError, stats.get)

    @patch("jnpr.junos.Device.execute")
    def test_table_with_item_without_view(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        yaml_data = """
---
EthernetSwitchStatisticsIterTable:
  command: show chassis ethernet-switch statistics
  item: Statistics for port (\d) connected to device (FPC\d)
  key:
    - port
    - fpc
"""
        globals().update(
            FactoryLoader().load(
                yaml.load(yaml_data, Loader=yamlordereddictloader.Loader)
            )
        )
        stats = EthernetSwitchStatisticsIterTable(self.dev)
        stats = stats.get()
        self.assertEqual(
            dict(stats),
            {
                (1, "FPC1"): {
                    "RX Broadcast Packets": 9206817,
                    "RX Byte Counter": 320925468,
                    "RX Packets 1024-1518 Octets": 3200039,
                    "RX Packets 512-1023 Octets": 4428661,
                    "TX Packets 128-255 Octets": 6738243,
                    "TX Packets 64 Octets": 142545489,
                    "TX Packets 65-127 Octets": 83498558,
                },
                (2, "FPC2"): {
                    "RX Byte Counter": 133138157,
                    "RX Packets 1024-1518 Octets": 7994417,
                    "RX Packets 128-255 Octets": 5848046,
                    "RX Packets 256-511 Octets": 14518495,
                    "RX Packets 512-1023 Octets": 33598800,
                    "RX Packets 64 Octets": 69281885,
                    "RX Packets 65-127 Octets": 98793558,
                    "TX Broadcast Packets": 46011330,
                    "TX Byte Counter": 12099160,
                    "TX Packets 128-255 Octets": 11245893,
                    "TX Packets 256-511 Octets": 55746,
                    "TX Packets 512-1023 Octets": 3669,
                    "TX Packets 64 Octets": 140666613,
                    "TX Packets 65-127 Octets": 105545277,
                },
                (4, "FPC4"): {
                    "RX 1519-1522 Good Vlan frms": 0,
                    "RX Align Errors": 0,
                    "RX Broadcast Packets": 9216795,
                    "RX Byte Counter": 361322476,
                    "RX Control Frame Counter": 0,
                    "RX FCS Errors": 0,
                    "RX False Carrier Errors": 0,
                    "RX Fragments": 0,
                    "RX Jabbers": 0,
                    "RX MTU Exceed Counter": 0,
                    "RX Multicast Packets": 0,
                    "RX Octets": 212488240,
                    "RX Out of Range Length": 0,
                    "RX Oversize Packets": 0,
                    "RX Packets 1024-1518 Octets": 5524595,
                    "RX Packets 128-255 Octets": 7153230,
                    "RX Packets 1519-2047 Octets": 0,
                    "RX Packets 2048-4095 Octets": 0,
                    "RX Packets 256-511 Octets": 2130213,
                    "RX Packets 4096-9216 Octets": 0,
                    "RX Packets 512-1023 Octets": 24031621,
                    "RX Packets 64 Octets": 69309261,
                    "RX Packets 65-127 Octets": 104339320,
                    "RX Pause Frame Counter": 0,
                    "RX Symbol errors": 0,
                    "RX Undersize Packets": 0,
                    "RX Unsupported opcodes": 0,
                    "TX 1519-1522 Good Vlan frms": 0,
                    "TX Broadcast Packets": 45997099,
                    "TX Byte Counter": 725771059,
                    "TX Collision frames": 0,
                    "TX Excessive Collisions": 0,
                    "TX FCS Error Counter": 0,
                    "TX Fragment Counter": 0,
                    "TX Frame deferred Xmns": 0,
                    "TX Frame excessive deferl": 0,
                    "TX Jabbers": 0,
                    "TX Late Collisions": 0,
                    "TX MAC ctrl frames": 0,
                    "TX Mult. Collision frames": 0,
                    "TX Multicast Packets": 6,
                    "TX Octets": 246717004,
                    "TX Oversize Packets": 0,
                    "TX PAUSEMAC Ctrl Frames": 0,
                    "TX Packets 1024-1518 Octets": 72615,
                    "TX Packets 128-255 Octets": 15940774,
                    "TX Packets 1519-2047 Octets": 0,
                    "TX Packets 2048-4095 Octets": 0,
                    "TX Packets 256-511 Octets": 6737,
                    "TX Packets 4096-9216 Octets": 0,
                    "TX Packets 512-1023 Octets": 2934,
                    "TX Packets 64 Octets": 1397543,
                    "TX Packets 65-127 Octets": 91616401,
                    "TX Single Collision frames": 0,
                },
            },
        )

    @patch("jnpr.junos.Device.execute")
    def test_title_without_view(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        yaml_data = """
---
EthernetSwitchStatistics:
    command: show chassis ethernet-switch statistics
    view: EthernetSwitchStatisticsView

EthernetSwitchStatisticsView:
  fields:
    fpc0: _EthSwitchStatsFpc0Table
    fpc1: _EthSwitchStatsFpc1Table
    fpc2: _EthSwitchStatsFpc2Table
    fpc3: _EthSwitchStatsFpc3Table
    fpc4: _EthSwitchStatsFpc4Table
    fpc5: _EthSwitchStatsFpc5Table

_EthSwitchStatsFpc0Table:
  title: Statistics for port 0 connected to device FPC0

_EthSwitchStatsFpc1Table:
  title: Statistics for port 1 connected to device FPC1

_EthSwitchStatsFpc2Table:
  title: Statistics for port 2 connected to device FPC2

_EthSwitchStatsFpc3Table:
  title: Statistics for port 3 connected to device FPC3

_EthSwitchStatsFpc4Table:
  title: Statistics for port 4 connected to device FPC4

_EthSwitchStatsFpc5Table:
  title: Statistics for port 5 connected to device FPC5
"""
        globals().update(
            FactoryLoader().load(
                yaml.load(yaml_data, Loader=yamlordereddictloader.Loader)
            )
        )
        stats = EthernetSwitchStatistics(self.dev)
        stats = stats.get()
        self.assertEqual(
            dict(stats),
            {
                "fpc0": {},
                "fpc1": {
                    "RX Broadcast Packets": 9206817,
                    "RX Byte Counter": 320925468,
                    "RX Packets 1024-1518 Octets": 3200039,
                    "RX Packets 512-1023 Octets": 4428661,
                    "TX Packets 128-255 Octets": 6738243,
                    "TX Packets 64 Octets": 142545489,
                    "TX Packets 65-127 Octets": 83498558,
                },
                "fpc2": {
                    "RX Byte Counter": 133138157,
                    "RX Packets 1024-1518 Octets": 7994417,
                    "RX Packets 128-255 Octets": 5848046,
                    "RX Packets 256-511 Octets": 14518495,
                    "RX Packets 512-1023 Octets": 33598800,
                    "RX Packets 64 Octets": 69281885,
                    "RX Packets 65-127 Octets": 98793558,
                    "TX Broadcast Packets": 46011330,
                    "TX Byte Counter": 12099160,
                    "TX Packets 128-255 Octets": 11245893,
                    "TX Packets 256-511 Octets": 55746,
                    "TX Packets 512-1023 Octets": 3669,
                    "TX Packets 64 Octets": 140666613,
                    "TX Packets 65-127 Octets": 105545277,
                },
                "fpc3": {},
                "fpc4": {
                    "RX 1519-1522 Good Vlan frms": 0,
                    "RX Align Errors": 0,
                    "RX Broadcast Packets": 9216795,
                    "RX Byte Counter": 361322476,
                    "RX Control Frame Counter": 0,
                    "RX FCS Errors": 0,
                    "RX False Carrier Errors": 0,
                    "RX Fragments": 0,
                    "RX Jabbers": 0,
                    "RX MTU Exceed Counter": 0,
                    "RX Multicast Packets": 0,
                    "RX Octets": 212488240,
                    "RX Out of Range Length": 0,
                    "RX Oversize Packets": 0,
                    "RX Packets 1024-1518 Octets": 5524595,
                    "RX Packets 128-255 Octets": 7153230,
                    "RX Packets 1519-2047 Octets": 0,
                    "RX Packets 2048-4095 Octets": 0,
                    "RX Packets 256-511 Octets": 2130213,
                    "RX Packets 4096-9216 Octets": 0,
                    "RX Packets 512-1023 Octets": 24031621,
                    "RX Packets 64 Octets": 69309261,
                    "RX Packets 65-127 Octets": 104339320,
                    "RX Pause Frame Counter": 0,
                    "RX Symbol errors": 0,
                    "RX Undersize Packets": 0,
                    "RX Unsupported opcodes": 0,
                    "TX 1519-1522 Good Vlan frms": 0,
                    "TX Broadcast Packets": 45997099,
                    "TX Byte Counter": 725771059,
                    "TX Collision frames": 0,
                    "TX Excessive Collisions": 0,
                    "TX FCS Error Counter": 0,
                    "TX Fragment Counter": 0,
                    "TX Frame deferred Xmns": 0,
                    "TX Frame excessive deferl": 0,
                    "TX Jabbers": 0,
                    "TX Late Collisions": 0,
                    "TX MAC ctrl frames": 0,
                    "TX Mult. Collision frames": 0,
                    "TX Multicast Packets": 6,
                    "TX Octets": 246717004,
                    "TX Oversize Packets": 0,
                    "TX PAUSEMAC Ctrl Frames": 0,
                    "TX Packets 1024-1518 Octets": 72615,
                    "TX Packets 128-255 Octets": 15940774,
                    "TX Packets 1519-2047 Octets": 0,
                    "TX Packets 2048-4095 Octets": 0,
                    "TX Packets 256-511 Octets": 6737,
                    "TX Packets 4096-9216 Octets": 0,
                    "TX Packets 512-1023 Octets": 2934,
                    "TX Packets 64 Octets": 1397543,
                    "TX Packets 65-127 Octets": 91616401,
                    "TX Single Collision frames": 0,
                },
                "fpc5": {},
            },
        )

    @patch("jnpr.junos.Device.execute")
    def test_valueerror_with_no_target(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        yaml_data = """
---
ShowToePfePacketStatsTable:
  command: show toe pfe {{ pfe_instance }} {{ asic_type }} {{ asic_instance }} toe-inst {{ toe_instance }} packet-stats
  args:
    pfe_instance: 0
    asic_type: xm
    asic_instance: 0
    toe_instance: 0
  target: Null
  item: 'Stream (\d): halt flag is NOT set'
  key: stream
  view: ShowToePfePacketStatsView

ShowToePfePacketStatsView:
  fields:
    tx_packets: _ShowToePfePacketStatsStream_tx_packets
    tx_descriptors: _ShowToePfePacketStatsStream_tx_descriptors
    tx_rates: _ShowToePfePacketStatsStream_tx_rates
    tx_errors: _ShowToePfePacketStatsStream_tx_errors
    rx_packets: _ShowToePfePacketStatsStream_rx_packets
    rx_descriptors: _ShowToePfePacketStatsStream_rx_descriptors
    rx_rates: _ShowToePfePacketStatsStream_rx_rates
    rx_errors: _ShowToePfePacketStatsStream_rx_errors

_ShowToePfePacketStatsStream_tx_packets:
  title: 'TX Packets'
  delimiter: ':'

_ShowToePfePacketStatsStream_tx_descriptors:
  title: 'TX Descriptors'
  delimiter: ':'

_ShowToePfePacketStatsStream_tx_rates:
  title: 'TX Rates:'
  delimiter: ':'

_ShowToePfePacketStatsStream_tx_errors:
  title: 'TX Errors:'
  delimiter: ':'

_ShowToePfePacketStatsStream_rx_packets:
  title: 'RX Packets'
  delimiter: ':'

_ShowToePfePacketStatsStream_rx_descriptors:
  title: 'RX Descriptors'
  delimiter: ':'

_ShowToePfePacketStatsStream_rx_rates:
  title: 'RX Rates:'
  delimiter: ':'

_ShowToePfePacketStatsStream_rx_errors:
  title: 'RX Errors:'
  delimiter: ':'
"""
        globals().update(
            FactoryLoader().load(
                yaml.load(yaml_data, Loader=yamlordereddictloader.Loader)
            )
        )
        stats = ShowToePfePacketStatsTable(self.dev)
        self.assertRaises(ValueError, stats.get)

    @patch("jnpr.junos.Device.execute")
    def test_item_with_fields_delimiter(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        yaml_data = """
---
ShowToePfePacketStatsTable:
  command: show toe pfe {{ pfe_instance }} {{ asic_type }} {{ asic_instance }} toe-inst {{ toe_instance }} packet-stats
  args:
    pfe_instance: 0
    asic_type: xm
    asic_instance: 0
    toe_instance: 0
  target: Null
  item: 'Stream (\d): halt flag is NOT set'
  key: stream
  view: ShowToePfePacketStatsView

ShowToePfePacketStatsView:
  fields:
    tx_packets: _ShowToePfePacketStatsStream_tx_packets
    tx_descriptors: _ShowToePfePacketStatsStream_tx_descriptors
    tx_rates: _ShowToePfePacketStatsStream_tx_rates
    tx_errors: _ShowToePfePacketStatsStream_tx_errors
    rx_packets: _ShowToePfePacketStatsStream_rx_packets
    rx_descriptors: _ShowToePfePacketStatsStream_rx_descriptors
    rx_rates: _ShowToePfePacketStatsStream_rx_rates
    rx_errors: _ShowToePfePacketStatsStream_rx_errors

_ShowToePfePacketStatsStream_tx_packets:
  title: 'TX Packets'
  delimiter: ':'

_ShowToePfePacketStatsStream_tx_descriptors:
  title: 'TX Descriptors'
  delimiter: ':'

_ShowToePfePacketStatsStream_tx_rates:
  title: 'TX Rates:'
  delimiter: ':'

_ShowToePfePacketStatsStream_tx_errors:
  title: 'TX Errors:'
  delimiter: ':'

_ShowToePfePacketStatsStream_rx_packets:
  title: 'RX Packets'
  delimiter: ':'

_ShowToePfePacketStatsStream_rx_descriptors:
  title: 'RX Descriptors'
  delimiter: ':'

_ShowToePfePacketStatsStream_rx_rates:
  title: 'RX Rates:'
  delimiter: ':'

_ShowToePfePacketStatsStream_rx_errors:
  title: 'RX Errors:'
  delimiter: ':'
"""
        globals().update(
            FactoryLoader().load(
                yaml.load(yaml_data, Loader=yamlordereddictloader.Loader)
            )
        )
        stats = ShowToePfePacketStatsTable(self.dev)
        stats = stats.get(target="fpc1")
        self.assertEqual(
            dict(stats),
            {
                0: {
                    "rx_descriptors": {
                        "completed": 12665827,
                        "recycle fails": 0,
                        "recycled": 12665827,
                    },
                    "rx_errors": {
                        "SOP/prev packet": 0,
                        "init descriptor idx invalid": 0,
                        "no prev packet": 0,
                        "no start packet": 0,
                    },
                    "rx_packets": {"accepted": 12665827},
                    "rx_rates": {
                        "bytes per second": 34,
                        "completed since last count": 102,
                        "descriptors per second": 1,
                        "packets per second": 1,
                    },
                    "tx_descriptors": {"accepted": 12665916, "completed": 12665916},
                    "tx_errors": {
                        "FIFO not initialized": 0,
                        "head descriptor invalid": 0,
                        "init descriptor idx invalid": 0,
                        "packet buffer out of range": 0,
                        "packet length out of range": 0,
                        "packet null": 0,
                    },
                    "tx_packets": {
                        "accepted": 12665916,
                        "rejected": 0,
                        "transferred": 12665916,
                    },
                    "tx_rates": {
                        "bytes per second": 34,
                        "descriptors completed since last count": 102,
                        "descriptors per second": 1,
                        "packets per second": 1,
                    },
                },
                1: {
                    "rx_descriptors": {
                        "completed": 12665827,
                        "recycle fails": 0,
                        "recycled": 12665827,
                    },
                    "rx_errors": {
                        "SOP/prev packet": 0,
                        "init descriptor idx invalid": 0,
                        "no prev packet": 0,
                        "no start packet": 0,
                    },
                    "rx_packets": {"accepted": 12665827},
                    "rx_rates": {
                        "bytes per second": 34,
                        "completed since last count": 102,
                        "descriptors per second": 1,
                        "packets per second": 1,
                    },
                    "tx_descriptors": {"accepted": 12665916, "completed": 12665916},
                    "tx_errors": {
                        "FIFO not initialized": 0,
                        "head descriptor invalid": 0,
                        "init descriptor idx invalid": 0,
                        "packet buffer out of range": 0,
                        "packet length out of range": 0,
                        "packet null": 0,
                    },
                    "tx_packets": {
                        "accepted": 12665916,
                        "rejected": 0,
                        "transferred": 12665916,
                    },
                    "tx_rates": {
                        "bytes per second": 34,
                        "descriptors completed since last count": 102,
                        "descriptors per second": 1,
                        "packets per second": 1,
                    },
                },
                2: {
                    "rx_descriptors": {
                        "completed": 0,
                        "recycle fails": 0,
                        "recycled": 0,
                    },
                    "rx_errors": {
                        "SOP/prev packet": 0,
                        "init descriptor idx invalid": 0,
                        "no prev packet": 0,
                        "no start packet": 0,
                    },
                    "rx_packets": {"accepted": 0},
                    "rx_rates": {
                        "bytes per second": 0,
                        "completed since last count": 0,
                        "descriptors per second": 0,
                        "packets per second": 0,
                    },
                    "tx_descriptors": {"accepted": 0, "completed": 0},
                    "tx_errors": {
                        "FIFO not initialized": 0,
                        "head descriptor invalid": 0,
                        "init descriptor idx invalid": 0,
                        "packet buffer out of range": 0,
                        "packet length out of range": 0,
                        "packet null": 0,
                    },
                    "tx_packets": {"accepted": 0, "rejected": 0, "transferred": 0},
                    "tx_rates": {
                        "bytes per second": 0,
                        "descriptors completed since last count": 0,
                        "descriptors per second": 0,
                        "packets per second": 0,
                    },
                },
                3: {
                    "rx_descriptors": {
                        "completed": 0,
                        "recycle fails": 0,
                        "recycled": 0,
                    },
                    "rx_errors": {
                        "SOP/prev packet": 0,
                        "init descriptor idx invalid": 0,
                        "no prev packet": 0,
                        "no start packet": 0,
                    },
                    "rx_packets": {"accepted": 0},
                    "rx_rates": {
                        "bytes per second": 0,
                        "completed since last count": 0,
                        "descriptors per second": 0,
                        "packets per second": 0,
                    },
                    "tx_descriptors": {"accepted": 0, "completed": 0},
                    "tx_errors": {
                        "FIFO not initialized": 0,
                        "head descriptor invalid": 0,
                        "init descriptor idx invalid": 0,
                        "packet buffer out of range": 0,
                        "packet length out of range": 0,
                        "packet null": 0,
                    },
                    "tx_packets": {"accepted": 0, "rejected": 0, "transferred": 0},
                    "tx_rates": {
                        "bytes per second": 0,
                        "descriptors completed since last count": 0,
                        "descriptors per second": 0,
                        "packets per second": 0,
                    },
                },
                4: {
                    "rx_descriptors": {
                        "completed": 67151069,
                        "recycle fails": 0,
                        "recycled": 67151069,
                    },
                    "rx_errors": {
                        "SOP/prev packet": 0,
                        "init descriptor idx invalid": 0,
                        "no prev packet": 0,
                        "no start packet": 0,
                    },
                    "rx_packets": {"accepted": 67151069},
                    "rx_rates": {
                        "bytes per second": 367,
                        "completed since last count": 552,
                        "descriptors per second": 5,
                        "packets per second": 5,
                    },
                    "tx_descriptors": {"accepted": 70932350, "completed": 70932350},
                    "tx_errors": {
                        "FIFO not initialized": 0,
                        "head descriptor invalid": 0,
                        "init descriptor idx invalid": 0,
                        "packet buffer out of range": 0,
                        "packet length out of range": 0,
                        "packet null": 0,
                    },
                    "tx_packets": {
                        "accepted": 70932350,
                        "rejected": 0,
                        "transferred": 70932350,
                    },
                    "tx_rates": {
                        "bytes per second": 301,
                        "descriptors completed since last count": 586,
                        "descriptors per second": 5,
                        "packets per second": 5,
                    },
                },
                5: {
                    "rx_descriptors": {
                        "completed": 0,
                        "recycle fails": 0,
                        "recycled": 0,
                    },
                    "rx_errors": {
                        "SOP/prev packet": 0,
                        "init descriptor idx invalid": 0,
                        "no prev packet": 0,
                        "no start packet": 0,
                    },
                    "rx_packets": {"accepted": 0},
                    "rx_rates": {
                        "bytes per second": 0,
                        "completed since last count": 0,
                        "descriptors per second": 0,
                        "packets per second": 0,
                    },
                    "tx_descriptors": {"accepted": 0, "completed": 0},
                    "tx_errors": {
                        "FIFO not initialized": 0,
                        "head descriptor invalid": 0,
                        "init descriptor idx invalid": 0,
                        "packet buffer out of range": 0,
                        "packet length out of range": 0,
                        "packet null": 0,
                    },
                    "tx_packets": {"accepted": 0, "rejected": 0, "transferred": 0},
                    "tx_rates": {
                        "bytes per second": 0,
                        "descriptors completed since last count": 0,
                        "descriptors per second": 0,
                        "packets per second": 0,
                    },
                },
                6: {
                    "rx_descriptors": {
                        "completed": 0,
                        "recycle fails": 0,
                        "recycled": 0,
                    },
                    "rx_errors": {
                        "SOP/prev packet": 0,
                        "init descriptor idx invalid": 0,
                        "no prev packet": 0,
                        "no start packet": 0,
                    },
                    "rx_packets": {"accepted": 0},
                    "rx_rates": {
                        "bytes per second": 0,
                        "completed since last count": 0,
                        "descriptors per second": 0,
                        "packets per second": 0,
                    },
                    "tx_descriptors": {"accepted": 0, "completed": 0},
                    "tx_errors": {
                        "FIFO not initialized": 0,
                        "head descriptor invalid": 0,
                        "init descriptor idx invalid": 0,
                        "packet buffer out of range": 0,
                        "packet length out of range": 0,
                        "packet null": 0,
                    },
                    "tx_packets": {"accepted": 0, "rejected": 0, "transferred": 0},
                    "tx_rates": {
                        "bytes per second": 0,
                        "descriptors completed since last count": 0,
                        "descriptors per second": 0,
                        "packets per second": 0,
                    },
                },
                7: {
                    "rx_descriptors": {
                        "completed": 0,
                        "recycle fails": 0,
                        "recycled": 0,
                    },
                    "rx_errors": {
                        "SOP/prev packet": 0,
                        "init descriptor idx invalid": 0,
                        "no prev packet": 0,
                        "no start packet": 0,
                    },
                    "rx_packets": {"accepted": 0},
                    "rx_rates": {
                        "bytes per second": 0,
                        "completed since last count": 0,
                        "descriptors per second": 0,
                        "packets per second": 0,
                    },
                    "tx_descriptors": {"accepted": 0, "completed": 0},
                    "tx_errors": {
                        "FIFO not initialized": 0,
                        "head descriptor invalid": 0,
                        "init descriptor idx invalid": 0,
                        "packet buffer out of range": 0,
                        "packet length out of range": 0,
                        "packet null": 0,
                    },
                    "tx_packets": {"accepted": 0, "rejected": 0, "transferred": 0},
                    "tx_rates": {
                        "bytes per second": 0,
                        "descriptors completed since last count": 0,
                        "descriptors per second": 0,
                        "packets per second": 0,
                    },
                },
            },
        )

    @patch("jnpr.junos.Device.execute")
    def test_table_eval_expression(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        yaml_data = """
---
XMChipInterruptStatsTable:
  command: show xmchip {{ chip_instance }} li interrupt-stats
  target: Null
  args:
    chip_instance: 0
  key:
    - li_block
    - name
  view: XMChipInterruptStatsView
  eval:
    total_interrupt: "reduce(lambda x,y: x+y, [v['interrupts'] for k,v in {{ data }}.items() if 'cookie_sz_err' in v.get('name')])"

XMChipInterruptStatsView:
  columns:
    li_block: LI Block
    name: Interrupt Name
    interrupts: Number of Interrupts
    last_occurance: Last Occurrence
    """
        globals().update(
            FactoryLoader().load(
                yaml.load(yaml_data, Loader=yamlordereddictloader.Loader)
            )
        )
        stats = XMChipInterruptStatsTable(self.dev)
        stats = stats.get(target="fpc1")
        self.assertEqual(stats["total_interrupt"], 34)

    @patch("jnpr.junos.Device.execute")
    def test_table_eval_expression_exception(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        yaml_data = """
---
XMChipInterruptStatsTable:
  command: show xmchip {{ chip_instance }} li interrupt-stats
  target: Null
  args:
    chip_instance: 0
  key:
    - li_block
    - name
  view: XMChipInterruptStatsView
  eval:
    total_interrupt: "xxxx"

XMChipInterruptStatsView:
  columns:
    li_block: LI Block
    name: Interrupt Name
    interrupts: Number of Interrupts
    last_occurance: Last Occurrence
        """
        globals().update(
            FactoryLoader().load(
                yaml.load(yaml_data, Loader=yamlordereddictloader.Loader)
            )
        )
        stats = XMChipInterruptStatsTable(self.dev)
        stats = stats.get(target="fpc1")
        self.assertEqual(stats["total_interrupt"], None)

    @patch("jnpr.junos.Device.execute")
    def test_table_eval_with_filters(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        yaml_data = """
---
FPCThreads:
  command: show threads
  target: fpc2
  key: Name
  view: FPCThreadView

FPCThreadView:
  columns:
    pid_pr: PID PR
    state: State
    name: Name
    stack: Stack Use
    time: Time (Last/Max/Total)
    cpu: cpu
  eval:
    cpu: "'{{ cpu }}'[:-1]"
  filters:
    - cpu
    - state
            """
        globals().update(
            FactoryLoader().load(
                yaml.load(yaml_data, Loader=yamlordereddictloader.Loader)
            )
        )
        stats = FPCThreads(self.dev)
        stats = stats.get()
        self.assertEqual(
            dict(stats),
            {
                "100ms Periodic": {"cpu": "0", "state": "asleep"},
                "10s Low Periodic": {"cpu": "0", "state": "asleep"},
                "10s Medium Periodic": {"cpu": "0", "state": "asleep"},
                "1s Low Periodic": {"cpu": "0", "state": "asleep"},
                "1s Medium Periodic": {"cpu": "0", "state": "asleep"},
                "50ms Periodic": {"cpu": "0", "state": "asleep"},
                "CFM Data thread": {"cpu": "0", "state": "asleep"},
                "CFM Manager": {"cpu": "0", "state": "asleep"},
                "CFP": {"cpu": "0", "state": "asleep"},
                "CLKSYNC Manager": {"cpu": "0", "state": "asleep"},
                "CLNS Err Input": {"cpu": "0", "state": "asleep"},
                "CLNS Option Input": {"cpu": "0", "state": "asleep"},
                "CXP": {"cpu": "0", "state": "asleep"},
                "Cassis Free Timer": {"cpu": "3", "state": "asleep"},
                "Cattle-Prod Daemon": {"cpu": "0", "state": "asleep"},
                "Console": {"cpu": "0", "state": "asleep"},
                "Cube Server": {"cpu": "0", "state": "asleep"},
                "DCC Background": {"cpu": "0", "state": "asleep"},
                "DDOS Policers": {"cpu": "0", "state": "asleep"},
                "DFW Alert": {"cpu": "0", "state": "asleep"},
                "DSX50ms": {"cpu": "0", "state": "asleep"},
                "DSXonesec": {"cpu": "0", "state": "asleep"},
                "Firmware Upgrade": {"cpu": "0", "state": "asleep"},
                "GR253": {"cpu": "0", "state": "asleep"},
                "HSL2": {"cpu": "0", "state": "asleep"},
                "Heap Accouting": {"cpu": "0", "state": "asleep"},
                "Host Loopback Periodic": {"cpu": "0", "state": "asleep"},
                "ICMP Input": {"cpu": "0", "state": "asleep"},
                "ICMP6 Input": {"cpu": "0", "state": "asleep"},
                "IFCM": {"cpu": "0", "state": "asleep"},
                "IGMP": {"cpu": "0", "state": "asleep"},
                "IGMP Input": {"cpu": "0", "state": "asleep"},
                "IP Option Input": {"cpu": "0", "state": "asleep"},
                "IP Reassembly": {"cpu": "0", "state": "asleep"},
                "IP6 Option Input": {"cpu": "0", "state": "asleep"},
                "IPC Test Daemon": {"cpu": "0", "state": "asleep"},
                "IPv4 PFE Control Background": {"cpu": "0", "state": "asleep"},
                "JNH Exception Counter Background Thread": {
                    "cpu": "0",
                    "state": "asleep",
                },
                "JNH KA Transmit": {"cpu": "0", "state": "asleep"},
                "JNH Partition Mem Recovery": {"cpu": "0", "state": "asleep"},
                "L2ALM Manager": {"cpu": "0", "state": "asleep"},
                "L2PD": {"cpu": "0", "state": "asleep"},
                "L2TP-SF KA Transmit": {"cpu": "0", "state": "asleep"},
                "LKUP ASIC UCODE Rebalance Service": {
                    "cpu": "1",
                    "state": "asleep",
                },
                "LKUP ASIC Wedge poll thread": {"cpu": "0", "state": "asleep"},
                "LU Background Service": {"cpu": "4", "state": "asleep"},
                "LU-CNTR Reader": {"cpu": "0", "state": "asleep"},
                "MSA300PIN": {"cpu": "0", "state": "asleep"},
                "Maintenance": {"cpu": "0", "state": "asleep"},
                "NH Probe Service": {"cpu": "0", "state": "asleep"},
                "OTN": {"cpu": "0", "state": "asleep"},
                "PFE Manager": {"cpu": "0", "state": "asleep"},
                "PFE Statistics": {"cpu": "0", "state": "asleep"},
                "PFEMAN SRRD Thread": {"cpu": "0", "state": "asleep"},
                "PFEMAN Service Thread": {"cpu": "0", "state": "asleep"},
                "PIC": {"cpu": "0", "state": "asleep"},
                "PIC Periodic": {"cpu": "0", "state": "asleep"},
                "PPM Data thread": {"cpu": "0", "state": "asleep"},
                "PPM Manager": {"cpu": "0", "state": "asleep"},
                "PQ3 PCI Periodic": {"cpu": "0", "state": "asleep"},
                "PRECL Chip Generic": {"cpu": "0", "state": "asleep"},
                "PZARB Timeout": {"cpu": "0", "state": "asleep"},
                "Pfesvcsor": {"cpu": "0", "state": "asleep"},
                "QSFP": {"cpu": "0", "state": "asleep"},
                "RCM Pfe Manager": {"cpu": "0", "state": "asleep"},
                "RDMAN": {"cpu": "0", "state": "asleep"},
                "RDP Input": {"cpu": "0", "state": "asleep"},
                "RDP Timers": {"cpu": "0", "state": "asleep"},
                "RFC2544 periodic": {"cpu": "0", "state": "asleep"},
                "RPM Msg thread": {"cpu": "0", "state": "asleep"},
                "RSMON syslog thread": {"cpu": "0", "state": "asleep"},
                "SFP": {"cpu": "0", "state": "asleep"},
                "SNTP Daemon": {"cpu": "0", "state": "asleep"},
                "Services TOD": {"cpu": "0", "state": "asleep"},
                "Sheaf Background": {"cpu": "0", "state": "asleep"},
                "Stats Page Ager": {"cpu": "0", "state": "asleep"},
                "Syslog": {"cpu": "0", "state": "asleep"},
                "TCP Receive": {"cpu": "0", "state": "asleep"},
                "TCP Timers": {"cpu": "0", "state": "asleep"},
                "TNP Hello": {"cpu": "0", "state": "asleep"},
                "TNPC CM": {"cpu": "0", "state": "asleep"},
                "TOE Coredump": {"cpu": "0", "state": "asleep"},
                "TTP Receive": {"cpu": "0", "state": "asleep"},
                "TTP Transmit": {"cpu": "0", "state": "asleep"},
                "TTRACE Creator": {"cpu": "0", "state": "asleep"},
                "TTRACE Tracer": {"cpu": "0", "state": "asleep"},
                "Timer Services": {"cpu": "0", "state": "asleep"},
                "Trap_Info Read PFE 0.0": {"cpu": "0", "state": "asleep"},
                "Trap_Info Read PFE 0.1": {"cpu": "0", "state": "asleep"},
                "Trap_Info Read PFE 1.0": {"cpu": "0", "state": "asleep"},
                "Trap_Info Read PFE 1.1": {"cpu": "0", "state": "asleep"},
                "UDP Input": {"cpu": "0", "state": "asleep"},
                "Ukern Syslog": {"cpu": "0", "state": "asleep"},
                "VBF MC Purge": {"cpu": "0", "state": "asleep"},
                "VBF PFE Events": {"cpu": "0", "state": "asleep"},
                "VBF Walker": {"cpu": "0", "state": "asleep"},
                "VRRP Manager": {"cpu": "0", "state": "asleep"},
                "Virtual Console": {"cpu": "0", "state": "asleep"},
                "XFP": {"cpu": "0", "state": "asleep"},
                "XM Chip Generic": {"cpu": "0", "state": "asleep"},
                "XM Chip Statistics": {"cpu": "0", "state": "asleep"},
                "XM Chip Wedge Detection and Recovery": {
                    "cpu": "0",
                    "state": "asleep",
                },
                "bulkget Manager": {"cpu": "0", "state": "asleep"},
                "cos halp stats daemon": {"cpu": "0", "state": "asleep"},
                "jnh errors daemon": {"cpu": "0", "state": "asleep"},
                "mac_db": {"cpu": "0", "state": "asleep"},
                "zlAprTaskzl303xx": {"cpu": "0", "state": "asleep"},
                "zlHybridTaskzl303xx": {"cpu": "0", "state": "asleep"},
                "zlInt08Taskzl303xx": {"cpu": "1", "state": "asleep"},
                "zlInt09Taskzl303xx": {"cpu": "0", "state": "asleep"},
                "zlPktTxSchedTaskzl303xx": {"cpu": "0", "state": "asleep"},
                "zlPtpTaskzl303xx": {"cpu": "0", "state": "asleep"},
                "zlSpllTaskzl303xx": {"cpu": "0", "state": "asleep"},
                "zlTimerTaskzl303xx": {"cpu": "0", "state": "asleep"},
                "zlTodMgrTaskzl303xx": {"cpu": "0", "state": "asleep"},
                "zlTsEngTaskzl303xx": {"cpu": "0", "state": "asleep"},
                "zlTxTsMgrTaskzl303xx": {"cpu": "0", "state": "asleep"},
            },
        )

    @patch("jnpr.junos.Device.execute")
    def test_new_line_in_data(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        yaml_data = """
---
CChipLoStatsTable:
  command: show xmchip {{ chip_instance }} lo stats 0
  target: fpc4
  args:
    chip_instance: 0
  title: 'LU  Parcel Name         Counter Name'
  key:
    - index
    - parcel
    - counter
  eval:
    cchip-lookup-out-errors: >
      sum([v['total'] for k,v in {{ data }}.items() if v['parcel']=='Error'])
  view: CChipLoStatsView

CChipLoStatsView:
  regex:
    index: '^\d+'
    parcel: '\w*(?=_)?\w*'
    counter: '(\w+(\s\w+)+)'
    total: '\d+'
    rate: '\d+ pps'
"""
        globals().update(
            FactoryLoader().load(
                yaml.load(yaml_data, Loader=yamlordereddictloader.Loader)
            )
        )
        stats = CChipLoStatsTable(self.dev)
        stats = stats.get(target="fpc0")
        self.assertEqual(stats["cchip-lookup-out-errors"], 500)

    @patch("jnpr.junos.Device.execute")
    def test_textfsm_table(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        yaml_data = """
---
ARPtable:
  command: show arp no-resolve
  platform: juniper_junos
  key: ip
  use_textfsm: True
  view: ARPview

ARPview:
    fields:
      mac: MAC
      ip: IP_ADDRESS
      interface: INTERFACE
      flag: FLAGS
"""
        globals().update(
            FactoryLoader().load(
                yaml.load(yaml_data, Loader=yamlordereddictloader.Loader)
            )
        )
        stats = ARPtable(self.dev)
        stats = stats.get()
        self.assertEqual(len(stats), 34)
        self.assertIn("10.221.128.201", stats)

    @patch("jnpr.junos.Device.execute")
    def test_textfsm_table_mutli_key(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        yaml_data = """
---
ARPtable:
    command: show arp no-resolve
    platform: juniper_junos
    key:
      - ip
      - mac
    use_textfsm: True
    view: ARPview

ARPview:
    fields:
        mac: MAC
        ip: IP_ADDRESS
        interface: INTERFACE
        flag: FLAGS
"""
        globals().update(
            FactoryLoader().load(
                yaml.load(yaml_data, Loader=yamlordereddictloader.Loader)
            )
        )
        stats = ARPtable(self.dev)
        stats = stats.get()
        self.assertIn(
            "('10.221.129.121', '56:68:ad:d8:10:f4')", json.loads(stats.to_json())
        )

    def _read_file(self, fname):
        from ncclient.xml_ import NCElement

        fpath = os.path.join(os.path.dirname(__file__), "rpc-reply", fname)
        foo = open(fpath).read()
        rpc_reply = NCElement(
            foo, self.dev._conn._device_handler.transform_reply()
        )._NCElement__doc
        return rpc_reply

    def _mock_manager(self, *args, **kwargs):
        if kwargs and "normalize" not in kwargs:
            device_params = kwargs["device_params"]
            device_handler = make_device_handler(device_params)
            session = SSHSession(device_handler)
            return Manager(session, device_handler)

        if args:
            if args[0].tag == "request-pfe-execute":
                file_name = (args[0].findtext("command")).replace(" ", "_")
                return self._read_file(file_name + ".xml")
            elif args[0].tag == "command":
                file_name = (args[0].text).replace(" ", "_")
                return self._read_file(file_name + ".xml")
