__author__ = "Nitin Kumar, Rick Sherman"
__credits__ = "Jeremy Schulman"

import unittest
from nose.plugins.attrib import attr
from mock import patch, MagicMock
from lxml import etree
import os

from jnpr.junos import Device
from jnpr.junos.facts.chassis import facts_chassis as chassis
from jnpr.junos.exception import ConnectNotMasterError

from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession
from jnpr.junos.utils.start_shell import StartShell


@attr('unit')
class TestChassis(unittest.TestCase):

    @patch('ncclient.manager.connect')
    def setUp(self, mock_connect):
        mock_connect.side_effect = self._mock_manager
        self.dev = Device(host='1.1.1.1', user='rick', password='password123',
                          gather_facts=False)
        self.dev.open()
        self.facts = {}

    @patch('jnpr.junos.Device.execute')
    def test_2RE_true(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        chassis(self.dev, self.facts)
        self.assertTrue(self.facts['2RE'])

    def test_chassis_exception_ConnectNotMasterError(self):
        xmldata = etree.XML('<rpc-reply><output>test</output></rpc-reply>')
        self.dev.rpc.get_chassis_inventory = MagicMock(side_effect=xmldata)
        self.assertRaises(ConnectNotMasterError, chassis, self.dev, self.facts)

    def test_chassis_exception_RuntimeError(self):
        xmldata = etree.XML('<rpc-reply><error>test</error></rpc-reply>')
        self.dev.rpc.get_chassis_inventory = MagicMock(side_effect=xmldata)
        chassis(self.dev, self.facts)
        self.assertFalse(self.facts['2RE'])
        self.assertEqual(self.facts['model'], self.facts['serialnumber'])

    def test_backup_chassis(self):
        xmldata = etree.XML('<rpc-reply><output>test</output></rpc-reply>')
        self.dev._RE = "backup"
        self.dev.rpc.get_chassis_inventory = MagicMock(side_effect=xmldata)
        xmldata = etree.XML('<rpc-reply><error>test</error></rpc-reply>')
        self.dev.rpc.get_software_information = MagicMock(side_effect=xmldata)
        chassis(self.dev, self.facts)
        self.assertEqual(self.dev._reRole, 'backup')

    @patch('ncclient.manager.connect')
    @patch('jnpr.junos.Device.execute')
    def test_device_chassis2(self, mock_connect, mock_execute):
        mock_connect.side_effect = self._mock_manager
        mock_execute.side_effect = self._mock_manager
        mock_shell = StartShell
        mock_shell.__enter__ = MagicMock(name="__enter__")
        mock_shell.__enter__.return_value = MagicMock(name="enterReturn")
        mock_shell._chan = MagicMock(name="_chan")
        mock_shell._client = MagicMock(name="_client")
        mock_shell.__enter__.return_value.run.return_value = ['hw.re.slotid: 1']
        self.dev2 = Device(
            host='2.2.2.2',
            user='rick',
            password='password123',
            routing_engine='master',
            gather_facts=False)
        xmldata = etree.XML('<rpc-reply><route-engine-information>'
                            '<route-engine><slot>0</slot>'
                            '<mastership-state>master</mastership-state>'
                            '</route-engine>'
                            '<route-engine><slot>1</slot>'
                            '<mastership-state>backup</mastership-state>'
                            '</route-engine></route-engine-information></rpc-reply>')
        self.dev2.rpc.get_route_engine_information = MagicMock(side_effect=xmldata)
        xmldata = etree.XML('<rpc-reply><configuration>'
                            '<groups><name>re1</name><system>'
                            '<host-name>irtb4-a1</host-name>'
                            '</system></groups>'
                            '</configuration></rpc-reply>')
        self.dev2.rpc.get_config = MagicMock(side_effect=xmldata)
        self.dev2.open()
        xmldata = etree.XML('<rpc-reply><output>test</output></rpc-reply>')
        self.dev2.rpc.get_software_information = MagicMock(side_effect=xmldata)
        chassis(self.dev2, self.facts)
        self.assertEqual(self.dev2._reRole, 'master')

    def _read_file(self, fname):
        from ncclient.xml_ import NCElement

        fpath = os.path.join(os.path.dirname(__file__),
                             'rpc-reply', fname)
        foo = open(fpath).read()

        rpc_reply = NCElement(foo,
                              self.dev._conn._device_handler
                              .transform_reply())._NCElement__doc[0]
        return rpc_reply

    def _mock_manager(self, *args, **kwargs):
        if kwargs:
            device_params = kwargs['device_params']
            device_handler = make_device_handler(device_params)
            session = SSHSession(device_handler)
            return Manager(session, device_handler)

        if args:
            return self._read_file('chassis_' + args[0].tag + '.xml')
