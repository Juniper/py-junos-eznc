__author__ = "Rick Sherman, Nitin Kumar"
__credits__ = "Jeremy Schulman"

import unittest
import os
from nose.plugins.attrib import attr
import yaml

from jnpr.junos import Device

from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession
from lxml import etree
from mock import MagicMock, patch

from jnpr.junos.factory import loadyaml
from jnpr.junos.factory.factory_loader import FactoryLoader

try:
    _YAML_ = loadyaml('lib/jnpr/junos/cfgro/srx')
except:
    # Try to load the template relative to test base
    try:
        _YAML_ = loadyaml(os.path.join(os.path.dirname(__file__), '../../..',
                                       'lib/jnpr/junos/cfgro/srx.yml'))
    except:
        raise

globals().update(_YAML_)

yaml_data = \
    """---
    UserTable:
      get: system/login/user
      required_keys:
        user: name
      view: userView

    userView:
      groups:
        auth: authentication
      fields:
        uid: uid
        class: class
        uidgroup: { uid: group }
        fullgroup: { full-name: group }
      fields_auth:
        pass: encrypted-password

    GroupTable:
        get: groups
        item:
        args_key: name
        options: {}
      """
globals().update(FactoryLoader().load(yaml.load(yaml_data)))


@attr('unit')
class TestFactoryCfgTable(unittest.TestCase):

    @patch('ncclient.manager.connect')
    def setUp(self, mock_connect):
        mock_connect.side_effect = self._mock_manager
        self.dev = Device(host='1.1.1.1', user='rick', password='password123',
                          gather_facts=False)
        self.dev.open()
        self.zit = ZoneIfsTable(self.dev)
        self.ut = UserTable(self.dev)

    def test_cfgtable_path(self):
        fname = 'user.xml'
        path = os.path.join(os.path.dirname(__file__),
                            'rpc-reply', fname)
        ut = UserTable(path=path)
        ut.get()
        self.assertEqual(ut[0].uid, '2000')

    def test_cfgtable_xml(self):
        fname = 'user.xml'
        xml = self._read_file(fname)
        ut = UserTable(xml=xml)
        ut.get()
        self.assertEqual(ut[0].uid, '2000')

    @patch('jnpr.junos.Device.execute')
    def test_cfgtable_get(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.zit.get(security_zone='untrust')
        self.assertEqual(len(self.zit), 1)

    @patch('jnpr.junos.Device.execute')
    def test_cfgtable_get_group(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.ut.get(user='test')
        self.assertEqual(self.ut[0]['uidgroup'], 'global')

    @patch('jnpr.junos.Device.execute')
    def test_cfgtable_get_namesonly(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.zit.get(security_zone='untrust', namesonly=True)
        self.assertEqual(self.zit._get_cmd.xpath('//@recurse')[0], 'false')

    @patch('jnpr.junos.Device.execute')
    def test_cfgtable_get_options(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.zit.get(security_zone='untrust', options={'inherit': 'defaults', 'groups': 'groups'})
        self.assertEqual(self.zit._get_opt, {'inherit': 'defaults', 'groups': 'groups'})

    @patch('jnpr.junos.Device.execute')
    def test_cfgtable_table_options(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        gt = GroupTable(self.dev)
        gt.get()
        self.assertEqual(gt._get_opt, {})

    def test_optable_get_key_required_error(self):
        self.assertRaises(ValueError, self.zit.get)

    @patch('jnpr.junos.Device.execute')
    def test_cfgtable_get_caller_provided_kvargs(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.zit.get(security_zone='untrust', key='test')
        self.assertTrue(mock_execute.called)

    def test_cfgtable_key_value_none(self):
        self.assertRaises(ValueError, self.zit.get, securityzone='untrust')

    @patch('jnpr.junos.Device.execute')
    def test_cfgtable_get_fields(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.zit._data_dict['get_fields'] = ['system-services']
        self.zit.get(security_zone='untrust', key='host-inbound-traffic')
        self.assertTrue('get_fields' in self.zit._data_dict)

    def test_cfgtable_dot_none_RuntimeError(self):
        ret_val = '<configuration><security><zones><test-zone>' \
                  '<interfaces recurse="false"/></test-zone></zones>' \
                  '</security></configuration>'
        self.zit._buildxml = MagicMock(return_value=etree.fromstring(ret_val))
        self.assertRaises(RuntimeError, self.zit.get, security_zone='abc')

    def _read_file(self, fname):
        from ncclient.xml_ import NCElement

        fpath = os.path.join(os.path.dirname(__file__),
                             'rpc-reply', fname)
        foo = open(fpath).read()

        if fname == 'user.xml':
            return etree.fromstring(foo)

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
            if args[0].xpath('//configuration/system/login/user'):
                return self._read_file('get-configuration-user.xml')
            else:
                return self._read_file(args[0].tag + '.xml')
