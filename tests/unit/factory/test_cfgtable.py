__author__ = "Rick Sherman, Nitin Kumar"
__credits__ = "Jeremy Schulman"

import unittest
import os
import sys

import nose2
import yaml

from jnpr.junos import Device

from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession
from lxml import etree
from mock import MagicMock, patch

from jnpr.junos.factory import loadyaml
from jnpr.junos.factory.factory_loader import FactoryLoader

try:
    _YAML_ = loadyaml("lib/jnpr/junos/cfgro/srx")
except:
    # Try to load the template relative to test base
    try:
        _YAML_ = loadyaml(
            os.path.join(
                os.path.dirname(__file__), "../../..", "lib/jnpr/junos/cfgro/srx.yml"
            )
        )
    except:
        raise

globals().update(_YAML_)

yaml_data = """---
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
globals().update(FactoryLoader().load(yaml.load(yaml_data, Loader=yaml.FullLoader)))

yaml_bgp_data = """---
  BgpTable:
    set: protocols/bgp/group
    key-field:
      - bgp_name
    view: BgpView

  BgpView:
    groups:
      neigh : neighbor
    fields:
      bgp_name   : { 'name' :
                        { 'type' : 'str', 'minValue' : 3, 'maxValue': 12 } }
      bgp_type   : {'type' :
                        {'type': { 'enum': ['external', 'internal'] },
                                    'default': 'external' } }
      local_addr : local-address
      peer       : { 'peer-as' :
                        { 'type' : 'int', 'minValue': 0, 'maxValue': 200} }
    fields_neigh:
      neigh      : name
   """

globals().update(FactoryLoader().load(yaml.load(yaml_bgp_data, Loader=yaml.FullLoader)))


@unittest.skipIf(sys.platform == "win32", "will work for windows in coming days")
class TestFactoryCfgTable(unittest.TestCase):
    @patch("ncclient.manager.connect")
    def setUp(self, mock_connect):
        mock_connect.side_effect = self._mock_manager
        self.dev = Device(
            host="1.1.1.1", user="rick", password="password123", gather_facts=False
        )
        self.dev.open()
        self.zit = ZoneIfsTable(self.dev)
        self.ut = UserTable(self.dev)
        self.bgp = BgpTable(self.dev)

    def test_cfgtable_path(self):
        fname = "user.xml"
        path = os.path.join(os.path.dirname(__file__), "rpc-reply", fname)
        ut = UserTable(path=path)
        ut.get()
        self.assertEqual(ut[0].uid, "2000")

    def test_cfgtable_xml(self):
        fname = "user.xml"
        xml = self._read_file(fname)
        ut = UserTable(xml=xml)
        ut.get()
        self.assertEqual(ut[0].uid, "2000")

    @patch("jnpr.junos.Device.execute")
    def test_cfgtable_junos(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.dev.ON_JUNOS = True
        self.ut.get(user="test")
        self.assertEqual(self.ut[0]["uidgroup"], "global")

    @patch("jnpr.junos.Device.execute")
    @patch("jnpr.junos.jxml.conf_transform")
    def test_cfgtable_junos1(self, mock_jxml, mock_execute):
        mock_execute.side_effect = self._mock_manager
        mock_jxml.result_value = None
        with patch.dict("sys.modules", junos=MagicMock()):
            import junos

            self.dev.ON_JUNOS = True
            self.bgp.get()
            self.assertEqual(self.bgp.bgp_type, "external")

    @patch("jnpr.junos.Device.execute")
    @patch("jnpr.junos.jxml.conf_transform")
    def test_cfgtable_junos2(self, mock_jxml, mock_execute):
        mock_execute.side_effect = self._mock_manager
        mock_jxml.result_value = None
        with patch.dict("sys.modules", junos=MagicMock()):
            import junos

            junos.Junos_Configuration = None
            self.dev.ON_JUNOS = True
            self.bgp.get()
            self.assertEqual(self.bgp.bgp_type, "external")

    @patch("jnpr.junos.Device.execute")
    def test_cfgtable_get(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.zit.get(security_zone="untrust")
        self.assertEqual(len(self.zit), 1)

    @patch("jnpr.junos.Device.execute")
    def test_cfgtable_get_group(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.ut.get(user="test")
        self.assertEqual(self.ut[0]["uidgroup"], "global")

    @patch("jnpr.junos.Device.execute")
    def test_cfgtable_get_namesonly(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.zit.get(security_zone="untrust", namesonly=True)
        self.assertEqual(self.zit._get_cmd.xpath("//@recurse")[0], "false")

    @patch("jnpr.junos.Device.execute")
    def test_cfgtable_get_options(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.zit.get(
            security_zone="untrust", options={"inherit": "defaults", "groups": "groups"}
        )
        self.assertEqual(self.zit._get_opt, {"inherit": "defaults", "groups": "groups"})

    @patch("jnpr.junos.Device.execute")
    def test_cfgtable_table_options(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        gt = GroupTable(self.dev)
        gt.get()
        self.assertEqual(gt._get_opt, {})

    def test_optable_get_key_required_error(self):
        self.assertRaises(ValueError, self.zit.get)

    @patch("jnpr.junos.Device.execute")
    def test_cfgtable_get_caller_provided_kvargs(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.zit.get(security_zone="untrust", key="test")
        self.assertTrue(mock_execute.called)

    def test_cfgtable_key_value_none(self):
        self.assertRaises(ValueError, self.zit.get, securityzone="untrust")

    @patch("jnpr.junos.Device.execute")
    def test_cfgtable_get_fields(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.zit._data_dict["get_fields"] = ["system-services"]
        self.zit.get(security_zone="untrust", key="host-inbound-traffic")
        self.assertTrue("get_fields" in self.zit._data_dict)

    def test_cfgtable_dot_none_RuntimeError(self):
        ret_val = (
            "<configuration><security><zones><test-zone>"
            '<interfaces recurse="false"/></test-zone></zones>'
            "</security></configuration>"
        )
        self.zit._buildxml = MagicMock(return_value=etree.fromstring(ret_val))
        self.assertRaises(RuntimeError, self.zit.get, security_zone="abc")

    @patch("jnpr.junos.Device.execute")
    def test_cfgtable_set(self, mock_execute):
        self.bgp.rpc.lock_configuration = MagicMock()
        self.bgp.bgp_name = "external_1"
        self.bgp.append()
        self.bgp.set()
        xml = self.bgp.get_table_xml()
        self.assertEqual(xml.xpath("protocols/bgp/group/name")[0].text, "external_1")

    @patch("jnpr.junos.Device.execute")
    def test_cfgtable_set_inactive(self, mock_execute):
        yaml_auto_data = """---
           UserConfigTable1:
             set: system/login
             key-field:
               - username
             view: UserConfigView1

           UserConfigView1:
              groups:  
                auth: authentication
              fields:
                user: user
                username: user/name
                classname: { user/class : { 'type' : { 'enum' : ['operator', 'read-only', 'super-user'] } } }
                uid: { user/uid : { 'type' : 'int', 'minValue' : 100, 'maxValue' : 64000 } }
              fields_auth:
                password: user/encrypted-password
           """
        globals().update(
            FactoryLoader().load(yaml.load(yaml_auto_data, Loader=yaml.FullLoader))
        )
        at = UserConfigTable1(self.dev)
        at.rpc.lock_configuration = MagicMock()
        at.username = "user1"
        at.user = {"inactive": "inactive"}
        at.append()
        at.set()
        xml = at.get_table_xml()
        self.assertEqual(
            xml.xpath('system/login/user[@inactive="inactive"]/name')[0].text, "user1"
        )

    @patch("jnpr.junos.Device.execute")
    def test_cfgtable_set_bool(self, mock_execute):
        yaml_auto_data = """---
           UserConfigTable1:
             set: system/login
             key-field:
               - username
             view: UserConfigView1

           UserConfigView1:
              groups:
                auth: authentication
              fields:
                user: user
                username: user/name
                classname: { user/class : { 'type' : { 'enum' : ['operator', 'read-only', 'super-user'] } } }
                uid: { user/uid : { 'type' : bool , 'default' :False} }
              fields_auth:
                password: user/encrypted-password
           """
        globals().update(
            FactoryLoader().load(yaml.load(yaml_auto_data, Loader=yaml.FullLoader))
        )
        at = UserConfigTable1(self.dev)
        at.rpc.lock_configuration = MagicMock()
        at.username = True
        at.user = {"inactive": "inactive"}
        at.append()
        at.set()
        xml = at.get_table_xml()
        self.assertNotEqual(xml.xpath("system/login/user/name")[0].text, "user1")

    @patch("jnpr.junos.Device.execute")
    def test_cfgtable_load(self, mock_execute):
        self.bgp.rpc.lock_configuration = MagicMock()
        self.bgp.bgp_name = "external_1"
        self.bgp.append()
        self.bgp.bgp_name = "external_2"
        self.bgp.append()
        self.bgp.load()
        xml = self.bgp.get_table_xml()
        self.assertEqual(xml.xpath("protocols/bgp/group/name")[0].text, "external_1")
        self.assertEqual(xml.xpath("protocols/bgp/group/name")[1].text, "external_2")

    @patch("jnpr.junos.Device.execute")
    def test_cfgtable_set_group(self, mock_execute):
        self.bgp.rpc.lock_configuration = MagicMock()
        self.bgp.bgp_name = "external_1"
        self.bgp.neigh = ["30.30.10.10"]
        self.bgp.bgp_type = "external"
        self.bgp.append()
        self.bgp.set()
        xml = self.bgp.get_table_xml()
        self.assertEqual(xml.xpath("protocols/bgp/group/name")[0].text, "external_1")
        self.assertEqual(
            xml.xpath("protocols/bgp/group/neighbor/name")[0].text, "30.30.10.10"
        )
        self.assertEqual(xml.xpath("protocols/bgp/group/type")[0].text, "external")

    @patch("jnpr.junos.Device.execute")
    def test_cfgtable_dict_set(self, mock_execute):
        self.bgp.rpc.lock_configuration = MagicMock()
        self.bgp["bgp_name"] = "external_3"
        self.bgp.append()
        self.bgp.set()
        xml = self.bgp.get_table_xml()
        self.assertEqual(xml.xpath("protocols/bgp/group/name")[0].text, "external_3")

    @patch("jnpr.junos.Device.execute")
    def test_cfgtable_invalid_field_error(self, mock_execute):
        def invalid_field():
            self.bgp.xyz = "bad"

        self.assertRaises(ValueError, invalid_field)

    @patch("jnpr.junos.Device.execute")
    def test_cfgtable_invalid_field_dict_error(self, mock_execute):
        def invalid_field_dict():
            self.bgp["xyz"] = "bad"

        self.assertRaises(ValueError, invalid_field_dict)

    @patch("jnpr.junos.Device.execute")
    def test_cfgtable_set_no_key_error(self, mock_execute):
        self.assertRaises(ValueError, self.bgp.append)

    @patch("jnpr.junos.Device.execute")
    def test_cfgtable_enum_error(self, mock_execute):
        self.bgp.bgp_name = "external_1"
        self.bgp.bgp_type = "abc"
        self.assertRaises(ValueError, self.bgp.append)

    @patch("jnpr.junos.Device.execute")
    def test_cfgtable_str_min_max_value_error(self, mock_execute):
        self.bgp.bgp_name = "ex"
        self.assertRaises(ValueError, self.bgp.append)

    @patch("jnpr.junos.Device.execute")
    def test_cfgtable_int_min_max_value_error(self, mock_execute):
        self.bgp.bgp_name = "external_1"
        self.bgp.peer = 300
        self.assertRaises(ValueError, self.bgp.append)

    @patch("jnpr.junos.Device.execute")
    def test_cfgtable_invalid_field_value_error(self, mock_execute):
        self.bgp.bgp_name = "external_1"
        self.bgp.peer = [[100]]
        self.assertRaises(ValueError, self.bgp.append)

    @patch("jnpr.junos.Device.execute")
    def test_cfgtable_str_key_field(self, mock_execute):
        yaml_auto_data = """---
          AutoSysTable:
            set: routing-options/autonomous-system
            key-field:
              as_num
            view: AutoSysView

          AutoSysView:
            fields:
              as_num: as-number
           """
        globals().update(
            FactoryLoader().load(yaml.load(yaml_auto_data, Loader=yaml.FullLoader))
        )
        at = AutoSysTable(self.dev)
        at.rpc.lock_configuration = MagicMock()
        at.as_num = 100
        at.append()
        at.set()
        xml = at.get_table_xml()
        self.assertEqual(
            xml.xpath("routing-options/autonomous-system/as-number")[0].text, "100"
        )

    @patch("jnpr.junos.Device.execute")
    def test_cfgtable_field_value_xpath(self, mock_execute):
        yaml_auto_data = """---
          AutoSysTable:
            set: routing-options
            key-field:
              as_num
            view: AutoSysView

          AutoSysView:
            fields:
              as_num: autonomous-system/as-number
           """
        globals().update(
            FactoryLoader().load(yaml.load(yaml_auto_data, Loader=yaml.FullLoader))
        )
        at = AutoSysTable(self.dev)
        at.rpc.lock_configuration = MagicMock()
        at.as_num = 150
        at.append()
        at.set()
        xml = at.get_table_xml()
        self.assertEqual(
            xml.xpath("routing-options/autonomous-system/as-number")[0].text, "150"
        )

    @patch("jnpr.junos.Device.execute")
    def test_cfgtable_user_defined_type_error(self, mock_execute):
        yaml_auto_data = """---
          AutoSysTable:
            set: routing-options/autonomous-system
            key-field:
              - as_num
            view: AutoSysView

          AutoSysView:
            fields:
              as_num: {'as-number': {'type': {'UserDefined': ''}}}
           """
        globals().update(
            FactoryLoader().load(yaml.load(yaml_auto_data, Loader=yaml.FullLoader))
        )
        at = AutoSysTable(self.dev)
        at.rpc.lock_configuration = MagicMock()
        at.as_num = 100
        self.assertRaises(TypeError, at.append)

    @patch("jnpr.junos.Device.execute")
    def test_cfgtable_wrong_type_error(self, mock_execute):
        yaml_auto_data = """---
          AutoSysTable:
            set: routing-options/autonomous-system
            key-field:
              - as_num
            view: AutoSysView

          AutoSysView:
            fields:
              as_num: {'as-number' : { 'type' : 'int'} }
           """
        globals().update(
            FactoryLoader().load(yaml.load(yaml_auto_data, Loader=yaml.FullLoader))
        )
        at = AutoSysTable(self.dev)
        at.as_num = "100"
        self.assertRaises(TypeError, at.append)

    @patch("jnpr.junos.Device.execute")
    def test_cfgtable_unsupported_type_error(self, mock_execute):
        yaml_auto_data = """---
          AutoSysTable:
            set: routing-options/autonomous-system
            key-field:
              - as_num
            view: AutoSysView

          AutoSysView:
            fields:
              as_num: {'as-number' : { 'type' : 'interger'} }
           """
        globals().update(
            FactoryLoader().load(yaml.load(yaml_auto_data, Loader=yaml.FullLoader))
        )
        at = AutoSysTable(self.dev)
        at.as_num = 100
        self.assertRaises(TypeError, at.append)

    @patch("jnpr.junos.Device.execute")
    def test_cfgtable_enum_value_str_error(self, mock_execute):
        yaml_auto_data = """---
          AutoSysTable:
            set: routing-options/autonomous-system
            key-field:
              - as_num
            view: AutoSysView

          AutoSysView:
            fields:
              as_num: {'as-number' : {'type' : {'enum': '100'}}}
           """
        globals().update(
            FactoryLoader().load(yaml.load(yaml_auto_data, Loader=yaml.FullLoader))
        )
        at = AutoSysTable(self.dev)
        at.as_num = 100
        self.assertRaises(ValueError, at.append)

    @patch("jnpr.junos.Device.execute")
    def test_cfgtable_enum_value_type_error(self, mock_execute):
        yaml_auto_data = """---
          AutoSysTable:
            set: routing-options/autonomous-system
            key-field:
              - as_num
            view: AutoSysView

          AutoSysView:
            fields:
              as_num: {'as-number' : {'type' : {'enum': {'100': ''}}}}
           """
        globals().update(
            FactoryLoader().load(yaml.load(yaml_auto_data, Loader=yaml.FullLoader))
        )
        at = AutoSysTable(self.dev)
        at.as_num = 100
        self.assertRaises(TypeError, at.append)

    @patch("jnpr.junos.Device.execute")
    def test_cfgtable_invalid_type_error(self, mock_execute):
        yaml_auto_data = """---
          AutoSysTable:
            set: routing-options/autonomous-system
            key-field:
              - as_num
            view: AutoSysView

          AutoSysView:
            fields:
              as_num: {'as-number': {'type': ['abc']}}
           """
        globals().update(
            FactoryLoader().load(yaml.load(yaml_auto_data, Loader=yaml.FullLoader))
        )
        at = AutoSysTable(self.dev)
        at.as_num = 100
        self.assertRaises(TypeError, at.append)

    @patch("jnpr.junos.Device.execute")
    def test_cfgtable_invalid_key_field_type_error(self, mock_execute):
        yaml_auto_data = """---
          AutoSysTable:
            set: routing-options/autonomous-system
            key-field:
              as_num : as-number
            view: AutoSysView

          AutoSysView:
            fields:
              as_num: as-number
           """
        globals().update(
            FactoryLoader().load(yaml.load(yaml_auto_data, Loader=yaml.FullLoader))
        )
        self.assertRaises(TypeError, AutoSysTable, self.dev)

    @patch("jnpr.junos.Device.execute")
    def test_cfgtable_invalid_key_field_not_defined_error(self, mock_execute):
        yaml_auto_data = """---
          AutoSysTable:
            set: routing-options/autonomous-system
            view: AutoSysView

          AutoSysView:
            fields:
              as_num: as-number
           """
        globals().update(
            FactoryLoader().load(yaml.load(yaml_auto_data, Loader=yaml.FullLoader))
        )
        self.assertRaises(ValueError, AutoSysTable, self.dev)

    @patch("jnpr.junos.Device.execute")
    def test_cfgtable_invalid_view_not_defined_type_error(self, mock_execute):
        yaml_auto_data = """---
          AutoSysTable:
            set: routing-options/autonomous-system
           """
        globals().update(
            FactoryLoader().load(yaml.load(yaml_auto_data, Loader=yaml.FullLoader))
        )
        self.assertRaises(ValueError, AutoSysTable, self.dev)

    @patch("jnpr.junos.Device.execute")
    def test_cfgtable_set_append_not_call_error(self, mock_execute):
        self.bgp.rpc.lock_configuration = MagicMock()
        self.bgp["bgp_name"] = "external_3"
        self.assertRaises(RuntimeError, self.bgp.set)

    @patch("jnpr.junos.Device.execute")
    def test_cfgtable_load_append_not_call_error(self, mock_execute):
        self.bgp["bgp_name"] = "external_3"
        self.assertRaises(RuntimeError, self.bgp.load)

    @patch("jnpr.junos.Device.execute")
    def test_cfgtable_unfreeze(self, mock_execute):
        self.bgp._unfreeze()
        self.assertEqual(self.bgp._CfgTable__isfrozen, False)

    @patch("jnpr.junos.Device.execute")
    @patch("jnpr.junos.utils.config.Config.lock")
    @patch("jnpr.junos.utils.config.Config.unlock")
    def test_cfgtable_with_block(self, mock_execute, mock_unlock, mock_lock):
        with BgpTable(self.dev, mode="exclusive") as bgp:
            bgp.rpc.lock_configuration = MagicMock()
            bgp.bgp_name = "external_1"
            bgp.append()
            bgp.load()
        self.assertTrue(mock_lock.called and mock_unlock.called)

    def _read_file(self, fname):
        from ncclient.xml_ import NCElement

        fpath = os.path.join(os.path.dirname(__file__), "rpc-reply", fname)

        foo = open(fpath).read()

        if fname == "user.xml":
            return etree.fromstring(foo)

        rpc_reply = NCElement(
            foo, self.dev._conn._device_handler.transform_reply()
        )._NCElement__doc[0]
        return rpc_reply

    def _mock_manager(self, *args, **kwargs):
        if kwargs:
            device_params = kwargs["device_params"]
            device_handler = make_device_handler(device_params)
            session = SSHSession(device_handler)
            return Manager(session, device_handler)

        if args:
            if args[0].xpath("//configuration/system/login/user"):
                return self._read_file("get-configuration-user.xml")
            else:
                return self._read_file(args[0].tag + ".xml")
