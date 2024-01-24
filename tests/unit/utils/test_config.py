import unittest
import sys
import nose2

from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos.exception import (
    RpcError,
    LockError,
    UnlockError,
    CommitError,
    RpcTimeoutError,
    ConfigLoadError,
    ConnectClosedError,
)

import ncclient
from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession
from ncclient.operations import RPCError, RPCReply

from mock import MagicMock, patch
from lxml import etree
import os

__author__ = "Nitin Kumar, Rick Sherman"
__credits__ = "Jeremy Schulman"

if sys.version < "3":
    builtin_string = "__builtin__"
else:
    builtin_string = "builtins"


class TestConfig(unittest.TestCase):
    @patch("ncclient.manager.connect")
    def setUp(self, mock_connect):
        mock_connect.side_effect = self._mock_manager

        self.dev = Device(
            host="1.1.1.1", user="test", password="test123", gather_facts=False
        )
        self.dev.open()
        self.conf = Config(self.dev)

    @patch("ncclient.operations.session.CloseSession.request")
    def tearDown(self, mock_session):
        self.dev.close()

    def test_config_constructor(self):
        self.assertTrue(isinstance(self.conf._dev, Device))

    def test_config_confirm_true(self):
        self.conf.rpc.commit_configuration = MagicMock()
        self.conf.commit(confirm=True)
        self.conf.rpc.commit_configuration.assert_called_with(confirmed=True)

    def test_config_commit_confirm(self):
        self.conf.rpc.commit_configuration = MagicMock()
        self.conf.commit(confirm=10)
        self.conf.rpc.commit_configuration.assert_called_with(
            **{"confirm-timeout": "10", "confirmed": True}
        )

    def test_config_commit_comment(self):
        self.conf.rpc.commit_configuration = MagicMock()
        self.conf.commit(comment="Test")
        self.conf.rpc.commit_configuration.assert_called_with(log="Test")

    def test_config_commit_sync(self):
        self.conf.rpc.commit_configuration = MagicMock()
        self.conf.commit(sync=True)
        self.conf.rpc.commit_configuration.assert_called_with(synchronize=True)

    def test_config_commit_force_sync(self):
        self.conf.rpc.commit_configuration = MagicMock()
        self.conf.commit(force_sync=True)
        self.conf.rpc.commit_configuration.assert_called_with(
            **{"synchronize": True, "force-synchronize": True}
        )

    def test_config_commit_timeout(self):
        self.conf.rpc.commit_configuration = MagicMock()
        self.conf.commit(timeout=60)
        self.conf.rpc.commit_configuration.assert_called_with(dev_timeout=60)

    def test_config_commit_full(self):
        self.conf.rpc.commit_configuration = MagicMock()
        self.conf.commit(full=True)
        self.conf.rpc.commit_configuration.assert_called_with(full=True)

    def test_config_commit_detail(self):
        self.conf.rpc.commit_configuration = MagicMock()
        self.conf.rpc.commit_configuration.return_value = "<mockdetail/>"
        self.assertEqual("<mockdetail/>", self.conf.commit(detail=True))
        self.conf.rpc.commit_configuration.assert_called_with({"detail": "detail"})

    def test_config_commit_combination(self):
        self.conf.rpc.commit_configuration = MagicMock()
        self.conf.rpc.commit_configuration.return_value = "<moredetail/>"
        self.assertEqual(
            "<moredetail/>", self.conf.commit(detail=True, force_sync=True, full=True)
        )
        self.conf.rpc.commit_configuration.assert_called_with(
            {"detail": "detail"},
            **{"synchronize": True, "full": True, "force-synchronize": True}
        )

    @patch("jnpr.junos.utils.config.JXML.remove_namespaces")
    def test_config_commit_xml_exception(self, mock_jxml):
        class MyException(Exception):
            xml = etree.fromstring("<test/>")

        self.conf.rpc.commit_configuration = MagicMock(side_effect=MyException)
        self.assertRaises(CommitError, self.conf.commit)

    def test_config_commit_exception(self):
        class MyException(Exception):
            pass

        self.conf.rpc.commit_configuration = MagicMock(side_effect=MyException)
        self.assertRaises(MyException, self.conf.commit)

    def test_config_commit_exception_RpcError(self):
        ex = RpcError(rsp="ok")
        self.conf.rpc.commit_configuration = MagicMock(side_effect=ex)
        self.assertTrue(self.conf.commit())
        import xml.etree.ElementTree as ET

        xmldata = """<data><company name="Juniper">
            <code>pyez</code>
            <year>2013</year>
            </company></data>"""
        root = ET.fromstring(xmldata)
        el = root.find("company")
        ex = RpcError(rsp=el)
        self.conf.rpc.commit_configuration = MagicMock(side_effect=ex)
        self.assertRaises(CommitError, self.conf.commit)

    def test_commit_check(self):
        self.conf.rpc.commit_configuration = MagicMock()
        self.assertTrue(self.conf.commit_check())

    # @patch('jnpr.junos.utils.config.JXML.rpc_error')
    def test_commit_check_exception(self):
        class MyException(Exception):
            xml = etree.fromstring(
                """
            <rpc-reply>
<rpc-error>
<error-type>protocol</error-type>
<error-tag>operation-failed</error-tag>
<error-severity>error</error-severity>
<error-message>permission denied</error-message>
<error-info>
<bad-element>system</bad-element>
</error-info>
</rpc-error>
</rpc-reply>
            """
            )

        self.conf.rpc.commit_configuration = MagicMock(side_effect=MyException)
        # with self.assertRaises(AttributeError):
        self.assertDictEqual(
            self.conf.commit_check(),
            {
                "source": None,
                "message": "permission denied",
                "bad_element": "system",
                "severity": "error",
                "edit_path": None,
            },
        )

    def test_config_commit_check_exception_RpcError(self):
        ex = RpcError(rsp="ok")
        self.conf.rpc.commit_configuration = MagicMock(side_effect=ex)
        self.assertTrue(self.conf.commit_check())
        import xml.etree.ElementTree as ET

        xmldata = """<data><company name="Juniper">
            <code>pyez</code>
            <year>2013</year>
            </company></data>"""
        root = ET.fromstring(xmldata)
        el = root.find("company")
        ex = RpcError(rsp=el)
        self.conf.rpc.commit_configuration = MagicMock(side_effect=ex)
        self.assertRaises(CommitError, self.conf.commit_check)

    def test_config_diff(self):
        self.conf.rpc.get_configuration = MagicMock()
        self.conf.diff()
        self.conf.rpc.get_configuration.assert_called_with(
            {"compare": "rollback", "rollback": "0", "format": "text"},
            ignore_warning=False,
        )

    def test_config_diff_use_fast_diff(self):
        self.conf.rpc.get_configuration = MagicMock()
        self.conf.diff(use_fast_diff=True)
        self.conf.rpc.get_configuration.assert_called_with(
            {
                "compare": "rollback",
                "rollback": "0",
                "format": "text",
                "use-fast-diff": "yes",
            },
            ignore_warning=False,
        )

    def test_config_diff_use_fast_diff_rb_id_gt_0(self):
        self.conf.rpc.get_configuration = MagicMock()
        with self.assertRaises(ValueError):
            self.conf.diff(use_fast_diff=True, rb_id=1)

    def test_config_diff_exception_severity_warning(self):
        rpc_xml = """
            <rpc-error>
            <error-severity>warning</error-severity>
            <error-info><bad-element>bgp</bad-element></error-info>
            <error-message>mgd: statement must contain additional statements</error-message>
        </rpc-error>
        """
        rsp = etree.XML(rpc_xml)
        self.conf.rpc.get_configuration = MagicMock(side_effect=RpcError(rsp=rsp))
        self.assertEqual(self.conf.diff(), "Unable to parse diff from response!")

    def test_config_diff_exception_severity_warning_still_raise(self):
        rpc_xml = """
            <rpc-error>
            <error-severity>warning</error-severity>
            <error-info><bad-element>bgp</bad-element></error-info>
            <error-message>statement not found</error-message>
        </rpc-error>
        """
        rsp = etree.XML(rpc_xml)
        self.conf.rpc.get_configuration = MagicMock(side_effect=RpcError(rsp=rsp))
        self.assertRaises(RpcError, self.conf.diff)

    def test_config_pdiff(self):
        self.conf.diff = MagicMock(return_value="Stuff")
        self.conf.pdiff()
        self.conf.diff.assert_called_once_with(0, False, False)

    def test_config_diff_rpc_timeout(self):
        ex = RpcTimeoutError(self.dev, None, 10)
        self.conf.rpc.get_configuration = MagicMock(side_effect=ex)
        self.assertRaises(RpcTimeoutError, self.conf.diff)

    def test_config_load(self):
        self.assertRaises(RuntimeError, self.conf.load)

    def test_config_load_vargs_len(self):
        self.assertRaises(RuntimeError, self.conf.load, "test.xml")

    def test_config_load_len_with_format_set(self):
        self.conf.rpc.load_config = MagicMock(return_value="rpc_contents")
        self.assertEqual(self.conf.load("test.xml", format="set"), "rpc_contents")

    def test_config_load_len_with_format_xml(self):
        self.conf.rpc.load_config = MagicMock(return_value="rpc_contents")
        xmldata = """<snmp>
          <community>
            <name>iBGP</name>
          </community>
        </snmp>"""

        self.assertEqual(self.conf.load(xmldata, format="xml"), "rpc_contents")

    def test_config_load_len_with_format_text(self):
        self.conf.rpc.load_config = MagicMock(return_value="rpc_contents")
        textdata = """policy-options {
    prefix-list TEST1-NETS {
        100.0.0.0/24;
    }
    policy-statement TEST1-NETS {
        term TEST1 {
            from {
                prefix-list TEST1-NETS;
            }
            then accept;
        }
        term REJECT {
            then reject;
        }
    }
}"""

        self.assertEqual(self.conf.load(textdata), "rpc_contents")

    def test_config_load_with_format_json(self):
        self.conf.rpc.load_config = MagicMock(
            return_value=etree.fromstring(
                """<load-configuration-results>
                            <ok/>
                        </load-configuration-results>"""
            )
        )
        op = self.conf.load("test.json", format="json")
        self.assertEqual(op.tag, "load-configuration-results")
        self.assertEqual(self.conf.rpc.load_config.call_args[1]["format"], "json")

    @patch(builtin_string + ".open")
    def test_config_load_with_format_json_from_file_ext(self, mock_open):
        self.conf.rpc.load_config = MagicMock(
            return_value=etree.fromstring(
                """<load-configuration-results>
                            <ok/>
                        </load-configuration-results>"""
            )
        )
        op = self.conf.load(path="test.json")
        self.assertEqual(op.tag, "load-configuration-results")
        self.assertEqual(self.conf.rpc.load_config.call_args[1]["format"], "json")

    @patch(builtin_string + ".open")
    def test_config_load_update(self, mock_open):
        self.conf.rpc.load_config = MagicMock(
            return_value=etree.fromstring(
                """<load-configuration-results>
                            <ok/>
                        </load-configuration-results>"""
            )
        )
        op = self.conf.load(path="test.conf", update=True)
        self.assertEqual(op.tag, "load-configuration-results")
        self.assertEqual(self.conf.rpc.load_config.call_args[1]["format"], "text")

    def test_config_load_update_merge_overwrite(self):
        self.assertRaises(
            ValueError,
            self.conf.load,
            path="test.jnpr",
            update=True,
            merge=True,
            overwrite=True,
        )

    @patch(builtin_string + ".open")
    def test_config_load_lformat_byext_ValueError(self, mock_open):
        self.conf.rpc.load_config = MagicMock(return_value="rpc_contents")
        self.assertRaises(ValueError, self.conf.load, path="test.jnpr")

    def test_config_load_lset_format_ValueError(self):
        self.conf.rpc.load_config = MagicMock(return_value="rpc_contents")
        self.assertRaises(
            ValueError, self.conf.load, "test.xml", format="set", overwrite=True
        )

    @patch(builtin_string + ".open")
    @patch("jnpr.junos.utils.config.etree.XML")
    def test_config_load_path_xml(self, mock_etree, mock_open):
        self.conf.dev.Template = MagicMock()
        mock_etree.return_value = "rpc_contents"
        self.conf.rpc.load_config = MagicMock(return_value=mock_etree.return_value)
        self.assertEqual(self.conf.load(path="test.xml"), "rpc_contents")

    @patch(builtin_string + ".open")
    def test_config_load_path_text(self, mock_open):
        self.conf.rpc.load_config = MagicMock()
        self.conf.load(path="test.conf")
        self.assertEqual(self.conf.rpc.load_config.call_args[1]["format"], "text")

    @patch(builtin_string + ".open")
    def test_config_load_path_set(self, mock_open):
        self.conf.rpc.load_config = MagicMock()
        self.conf.load(path="test.set")
        self.assertEqual(self.conf.rpc.load_config.call_args[1]["action"], "set")

    @patch(builtin_string + ".open")
    def test_config_load_try_load_rpcerror(self, mock_open):
        ex = ConfigLoadError(
            rsp=etree.fromstring(
                (
                    """<load-configuration-results>
                <rpc-error>
                <error-severity>error</error-severity>
                <error-message>syntax error</error-message>
                </rpc-error>
                </load-configuration-results>"""
                )
            )
        )
        self.conf.rpc.load_config = MagicMock(side_effect=ex)
        self.assertRaises(ConfigLoadError, self.conf.load, path="config.conf")

    @patch(builtin_string + ".open")
    def test_config_load_try_load_rpctimeouterror(self, mock_open):
        ex = RpcTimeoutError(self.dev, None, 10)
        self.conf.rpc.load_config = MagicMock(side_effect=ex)
        self.assertRaises(RpcTimeoutError, self.conf.load, path="config.conf")

    @patch(builtin_string + ".open")
    def test_config_try_load_exception(self, mock_open):
        class OtherException(Exception):
            pass

        self.conf.rpc.load_config = MagicMock(side_effect=OtherException())
        self.assertRaises(OtherException, self.conf.load, path="config.conf")

    @patch("jnpr.junos.utils.config.etree.XML")
    def test_config_load_template_path(self, mock_etree):
        self.conf.rpc.load_config = MagicMock()
        self.conf.dev.Template = MagicMock()
        self.conf.load(template_path="test.xml")
        self.assertEqual(self.conf.rpc.load_config.call_args[1]["format"], "xml")

    def test_config_load_template(self):
        class Temp:
            filename = "abc.xml"
            render = MagicMock(return_value="<test/>")

        self.conf.rpc.load_config = MagicMock()
        self.conf.load(template=Temp)
        self.assertEqual(self.conf.rpc.load_config.call_args[1]["format"], "xml")

    def test_config_diff_exception(self):
        self.conf.rpc.get_configuration = MagicMock()
        self.assertRaises(ValueError, self.conf.diff, 51)
        self.assertRaises(ValueError, self.conf.diff, -1)

    def test_config_lock(self):
        self.conf.rpc.lock_configuration = MagicMock()
        self.assertTrue(self.conf.lock())

    @patch("jnpr.junos.utils.config.JXML.rpc_error")
    def test_config_lock_LockError(self, mock_jxml):
        ex = RpcError(rsp="ok")
        self.conf.rpc.lock_configuration = MagicMock(side_effect=ex)
        self.assertRaises(LockError, self.conf.lock)

    @patch("jnpr.junos.utils.config.JXML.rpc_error")
    def test_config_lock_ConnectClosedError(self, mock_jxml):
        ex = ConnectClosedError(dev=self)
        self.conf.rpc.lock_configuration = MagicMock(side_effect=ex)
        self.assertRaises(ConnectClosedError, self.conf.lock)

    @patch("jnpr.junos.utils.config.JXML.remove_namespaces")
    def test_config_lock_exception(self, mock_jxml):
        class MyException(Exception):
            xml = "test"

        self.conf.rpc.lock_configuration = MagicMock(side_effect=MyException)
        self.assertRaises(LockError, self.conf.lock)

    def test_config_unlock(self):
        self.conf.rpc.unlock_configuration = MagicMock()
        self.assertTrue(self.conf.unlock())

    @patch("jnpr.junos.utils.config.JXML.rpc_error")
    def test_config_unlock_LockError(self, mock_jxml):
        ex = RpcError(rsp="ok")
        self.conf.rpc.unlock_configuration = MagicMock(side_effect=ex)
        self.assertRaises(UnlockError, self.conf.unlock)

    @patch("jnpr.junos.utils.config.JXML.rpc_error")
    def test_config_unlock_ConnectClosedError(self, mock_jxml):
        ex = ConnectClosedError(dev=self)
        self.conf.rpc.unlock_configuration = MagicMock(side_effect=ex)
        self.assertRaises(ConnectClosedError, self.conf.unlock)

    @patch("jnpr.junos.utils.config.JXML.remove_namespaces")
    def test_config_unlock_exception(self, mock_jxml):
        class MyException(Exception):
            xml = "test"

        self.conf.rpc.unlock_configuration = MagicMock(side_effect=MyException)
        self.assertRaises(UnlockError, self.conf.unlock)

    def test_config_rollback(self):
        self.conf.rpc.load_configuration = MagicMock()
        self.assertTrue(self.conf.rollback())

    def test_config_rollback_exception(self):
        self.conf.rpc.load_configuration = MagicMock()
        self.assertRaises(ValueError, self.conf.rollback, 51)
        self.assertRaises(ValueError, self.conf.rollback, -1)

    @patch("jnpr.junos.Device.execute")
    def test_rescue_action_save(self, mock_exec):
        self.dev.request_save_rescue_configuration = MagicMock()
        self.assertTrue(self.conf.rescue("save"))

    @patch("jnpr.junos.Device.execute")
    def test_rescue_action_get_exception(self, mock_exec):
        self.dev.rpc.get_rescue_information = MagicMock(side_effect=Exception)
        self.assertTrue(self.conf.rescue("get") is None)

    @patch("jnpr.junos.Device.execute")
    def test_rescue_action_get(self, mock_exec):
        self.dev.rpc.get_rescue_information = MagicMock()
        self.dev.rpc.get_rescue_information.return_value = 1
        self.assertEqual(self.conf.rescue("get", format="xml"), 1)

    @patch("jnpr.junos.Device.execute")
    def test_rescue_action_delete(self, mock_exec):
        self.dev.rpc.request_delete_rescue_configuration = MagicMock()
        self.assertTrue(self.conf.rescue("delete"))

    @patch("jnpr.junos.Device.execute")
    def test_rescue_action_reload(self, mock_exec):
        self.dev.rpc.load_configuration = MagicMock()
        self.dev.rpc.load_configuration.return_value = True
        self.assertTrue(self.conf.rescue("reload"))

    @patch("jnpr.junos.Device.execute")
    def test_rescue_action_reload_exception(self, mock_exec):
        self.dev.rpc.load_configuration = MagicMock(side_effect=Exception)
        self.assertFalse(self.conf.rescue("reload"))

    @patch("jnpr.junos.Device.execute")
    def test_rescue_action_unsupported_action(self, mock_exec):
        self.assertRaises(ValueError, self.conf.rescue, "abc")

    def test_config_load_lset_from_rexp_xml(self):
        self.conf.rpc.load_config = MagicMock()
        conf = """<snmp><name>iBGP</name></snmp>"""
        self.conf.load(conf)
        self.assertEqual(self.conf.rpc.load_config.call_args[1]["format"], "xml")

    def test_config_load_lset_from_rexp_json(self):
        self.conf.rpc.load_config = MagicMock()
        conf = """{
            "configuration" : {
                "system" : {
                    "services" : {
                        "telnet" : [null]
                    }
                }
            }
        }"""
        self.conf.load(conf)
        self.assertEqual(self.conf.rpc.load_config.call_args[1]["format"], "json")

    def test_config_load_lset_from_rexp_set(self):
        self.conf.rpc.load_config = MagicMock()
        conf = """set system domain-name englab.nitin.net"""
        self.conf.load(conf)
        self.assertEqual(self.conf.rpc.load_config.call_args[1]["action"], "set")

    def test_config_load_lset_from_rexp_set_delete(self):
        self.conf.rpc.load_config = MagicMock()
        conf = """delete snmp"""
        self.conf.load(conf)
        self.assertEqual(self.conf.rpc.load_config.call_args[1]["action"], "set")

    def test_config_load_lset_from_rexp_set_rename(self):
        self.conf.rpc.load_config = MagicMock()
        conf = """rename firewall family inet filter f1 to filter f2"""
        self.conf.load(conf)
        self.assertEqual(self.conf.rpc.load_config.call_args[1]["action"], "set")

    def test_config_load_lset_from_rexp_insert(self):
        self.conf.rpc.load_config = MagicMock()
        conf = """insert policy-options policy-statement hop term 10 after 9"""
        self.conf.load(conf)
        self.assertEqual(self.conf.rpc.load_config.call_args[1]["action"], "set")

    def test_config_load_lset_from_rexp_set_activate(self):
        self.conf.rpc.load_config = MagicMock()
        conf = """activate system services ftp"""
        self.conf.load(conf)
        self.assertEqual(self.conf.rpc.load_config.call_args[1]["action"], "set")

    def test_config_load_lset_from_rexp_set_deactivate(self):
        self.conf.rpc.load_config = MagicMock()
        conf = """deactivate system services ftp"""
        self.conf.load(conf)
        self.assertEqual(self.conf.rpc.load_config.call_args[1]["action"], "set")

    def test_config_load_lset_from_rexp_set_annotate(self):
        self.conf.rpc.load_config = MagicMock()
        conf = """annotate system \"Annotation test\""""
        self.conf.load(conf)
        self.assertEqual(self.conf.rpc.load_config.call_args[1]["action"], "set")

    def test_config_load_lset_from_rexp_set_copy(self):
        self.conf.rpc.load_config = MagicMock()
        conf = """copy firewall family inet filter f1 to filter f2"""
        self.conf.load(conf)
        self.assertEqual(self.conf.rpc.load_config.call_args[1]["action"], "set")

    def test_config_load_lset_from_rexp_set_protect(self):
        self.conf.rpc.load_config = MagicMock()
        conf = """protect system services"""
        self.conf.load(conf)
        self.assertEqual(self.conf.rpc.load_config.call_args[1]["action"], "set")

    def test_config_load_lset_from_rexp_set_unprotect(self):
        self.conf.rpc.load_config = MagicMock()
        conf = """unprotect system services"""
        self.conf.load(conf)
        self.assertEqual(self.conf.rpc.load_config.call_args[1]["action"], "set")

    def test_config_load_lset_from_rexp_conf(self):
        self.conf.rpc.load_config = MagicMock()
        conf = """
            snmp {
                location USA;
                community iBGP {
                authorization read-only;
            }
            }"""
        self.conf.load(conf)
        self.assertEqual(self.conf.rpc.load_config.call_args[1]["format"], "text")

    def test_config_load_lset_from_rexp_conf_replace_tag(self):
        self.conf.rpc.load_config = MagicMock()
        conf = """replace:
            snmp {
                location USA;
                community iBGP {
                authorization read-only;
            }
            }"""
        self.conf.load(conf)
        self.assertEqual(self.conf.rpc.load_config.call_args[1]["format"], "text")
        self.assertEqual(self.conf.rpc.load_config.call_args[1]["action"], "replace")

    def test_config_load_lset_from_rexp_error(self):
        self.conf.rpc.load_config = MagicMock()
        conf = """test>"""
        self.assertRaises(RuntimeError, self.conf.load, conf)

    def test_load_merge_true(self):
        self.conf.rpc.load_config = MagicMock()
        conf = """
            snmp {
                location USA;
                community iBGP {
                authorization read-only;
            }
            }"""
        self.conf.load(conf, merge=True)
        self.assertFalse("action" in self.conf.rpc.load_config.call_args[1])

    def test_commit_RpcTimeoutError(self):
        ex = RpcTimeoutError(self.dev, None, 10)
        self.dev.rpc.commit_configuration = MagicMock(side_effect=ex)
        self.assertRaises(RpcTimeoutError, self.conf.commit)

    def test_commit_check_RpcTimeoutError(self):
        ex = RpcTimeoutError(self.dev, None, 10)
        self.dev.rpc.commit_configuration = MagicMock(side_effect=ex)
        self.assertRaises(RpcTimeoutError, self.conf.commit_check)

    def test_commit_configuration_multi_rpc_error(self):
        self.dev._conn.rpc = MagicMock(side_effect=self._mock_manager)
        try:
            self.dev.rpc.commit_configuration()
        except Exception as ex:
            self.assertTrue(isinstance(ex, RpcError))
            self.assertEqual(
                ex.message,
                "error: interface-range 'axp' is not defined\n"
                "error: interface-ranges expansion failed",
            )
            self.assertEqual(
                ex.errs,
                [
                    {
                        "source": None,
                        "message": "interface-range 'axp' is not defined",
                        "bad_element": None,
                        "severity": "error",
                        "edit_path": None,
                    },
                    {
                        "source": None,
                        "message": "interface-ranges expansion failed",
                        "bad_element": None,
                        "severity": "error",
                        "edit_path": None,
                    },
                ],
            )

    @patch("jnpr.junos.utils.config.Config.lock")
    @patch("jnpr.junos.utils.config.Config.unlock")
    def test_config_mode_exclusive(self, mock_unlock, mock_lock):
        with Config(self.dev, mode="exclusive") as conf:
            conf.rpc.load_config = MagicMock()
            conf.load("conf", format="set")
        self.assertTrue(mock_lock.called and mock_unlock.called)

    @patch("jnpr.junos.Device.execute")
    def test_config_mode_batch(self, mock_exec):
        self.dev.rpc.open_configuration = MagicMock()
        with Config(self.dev, mode="batch") as conf:
            conf.load("conf", format="set")
        self.dev.rpc.open_configuration.assert_called_with(batch=True)

    @patch("jnpr.junos.Device.execute")
    def test_config_mode_private(self, mock_exec):
        self.dev.rpc.open_configuration = MagicMock()
        with Config(self.dev, mode="private") as conf:
            conf.load("conf", format="set")
        self.dev.rpc.open_configuration.assert_called_with(private=True)

    @patch("jnpr.junos.Device.execute")
    def test_config_mode_dynamic(self, mock_exec):
        self.dev.rpc.open_configuration = MagicMock()
        with Config(self.dev, mode="dynamic") as conf:
            conf.load("conf", format="set")
        self.dev.rpc.open_configuration.assert_called_with(dynamic=True)

    @patch("jnpr.junos.Device.execute")
    def test_config_mode_ephemeral_default(self, mock_exec):
        self.dev.rpc.open_configuration = MagicMock()
        with Config(self.dev, mode="ephemeral") as conf:
            conf.load("conf", format="set")
        self.dev.rpc.open_configuration.assert_called_with(ephemeral=True)

    @patch("jnpr.junos.Device.execute")
    def test_config_mode_ephemeral_instance(self, mock_exec):
        self.dev.rpc.open_configuration = MagicMock()
        with Config(self.dev, mode="ephemeral", ephemeral_instance="xyz") as conf:
            conf.load("conf", format="set")
        self.dev.rpc.open_configuration.assert_called_with(ephemeral_instance="xyz")

    def test_config_unsupported_kwargs(self):
        self.dev.rpc.open_configuration = MagicMock()
        try:
            with Config(self.dev, mode="ephemeral", xyz="xyz") as conf:
                conf.load("conf", format="set")
        except Exception as ex:
            self.assertEqual(str(ex), "Unsupported argument provided to Config class")

    @patch("jnpr.junos.Device.execute")
    def test_config_mode_close_configuration_ex(self, mock_exec):
        self.dev.rpc.open_configuration = MagicMock()
        ex = RpcError(rsp="ok")
        ex.message = "Configuration database is not open"
        self.dev.rpc.close_configuration = MagicMock(side_effect=ex)
        try:
            with Config(self.dev, mode="batch") as conf:
                conf.load("conf", format="set")
        except Exception as ex:
            self.assertTrue(isinstance(ex, RpcError))
        self.assertTrue(self.dev.rpc.close_configuration.called)

    def test_config_mode_undefined(self):
        try:
            with Config(self.dev, mode="unknown") as conf:
                conf.load("conf", format="set")
        except Exception as ex:
            self.assertTrue(isinstance(ex, ValueError))

    @patch("jnpr.junos.Device.execute")
    @patch("jnpr.junos.utils.config.warnings")
    def test_config_mode_batch_open_configuration_ex(self, mock_warnings, mock_exec):
        rpc_xml = """
            <rpc-error>
            <error-severity>warning</error-severity>
            <error-info><bad-element>bgp</bad-element></error-info>
            <error-message>syntax error</error-message>
        </rpc-error>
        """
        rsp = etree.XML(rpc_xml)
        obj = RpcError(rsp=rsp)
        self.dev.rpc.open_configuration = MagicMock(side_effect=obj)
        with Config(self.dev, mode="batch") as conf:
            conf.load("conf", format="set")
        self.dev.rpc.open_configuration.assert_called_with(batch=True)

    @patch("jnpr.junos.Device.execute")
    @patch("jnpr.junos.utils.config.warnings")
    def test_config_mode_private_open_configuration_ex(self, mock_warnings, mock_exec):
        rpc_xml = """
            <rpc-error>
            <error-severity>warning</error-severity>
            <error-info><bad-element>bgp</bad-element></error-info>
            <error-message>syntax error</error-message>
        </rpc-error>
        """
        rsp = etree.XML(rpc_xml)
        obj = RpcError(rsp=rsp)
        self.dev.rpc.open_configuration = MagicMock(side_effect=obj)
        with Config(self.dev, mode="private") as conf:
            conf.load("conf", format="set")
        self.dev.rpc.open_configuration.assert_called_with(private=True)

    def test__enter__private_exception_RpcTimeoutError(self):
        ex = RpcTimeoutError(self.dev, None, 10)
        self.conf.rpc.open_configuration = MagicMock(side_effect=ex)
        self.assertRaises(
            RpcTimeoutError, Config.__enter__, Config(self.dev, mode="private")
        )

    def test__enter__private_exception_RpcError(self):
        rpc_xml = """<rpc-error>
            <error-severity>error</error-severity>
            <error-message>syntax error</error-message>
            </rpc-error>"""
        rsp = etree.XML(rpc_xml)
        self.conf.rpc.open_configuration = MagicMock(side_effect=RpcError(rsp=rsp))
        self.assertRaises(RpcError, Config.__enter__, Config(self.dev, mode="private"))

    def test__enter__dyanamic_exception_RpcError(self):
        rpc_xml = """<rpc-error>
            <error-severity>error</error-severity>
            <error-message>syntax error</error-message>
            </rpc-error>"""
        rsp = etree.XML(rpc_xml)
        self.conf.rpc.open_configuration = MagicMock(side_effect=RpcError(rsp=rsp))
        self.assertRaises(RpcError, Config.__enter__, Config(self.dev, mode="dynamic"))

    def test__enter__batch_exception_RpcTimeoutError(self):
        ex = RpcTimeoutError(self.dev, None, 10)
        self.conf.rpc.open_configuration = MagicMock(side_effect=ex)
        self.assertRaises(
            RpcTimeoutError, Config.__enter__, Config(self.dev, mode="batch")
        )

    def test__enter__batch_exception_RpcError(self):
        rpc_xml = """<rpc-error>
            <error-severity>error</error-severity>
            <error-message>syntax error</error-message>
            </rpc-error>"""
        rsp = etree.XML(rpc_xml)
        self.conf.rpc.open_configuration = MagicMock(side_effect=RpcError(rsp=rsp))
        self.assertRaises(RpcError, Config.__enter__, Config(self.dev, mode="batch"))

    def test_config_load_url(self):
        self.conf.rpc.load_config = MagicMock()
        self.conf.load(url="/var/home/user/golden.conf")
        self.assertEqual(
            self.conf.rpc.load_config.call_args[1]["url"], "/var/home/user/golden.conf"
        )

    @patch("jnpr.junos.Device.execute")
    def test_load_config_patch(self, mock_exec):
        conf = """[edit system]
            -  host-name pakzds904;
            +  host-name pakzds904_set;
            """
        self.conf.load(conf, format="text", patch=True)
        self.assertEqual(mock_exec.call_args[0][0].tag, "load-configuration")
        self.assertEqual(
            mock_exec.call_args[0][0].attrib, {"format": "text", "action": "patch"}
        )

    @patch("jnpr.junos.Device.execute")
    def test_load_config_text(self, mock_exec):
        textdata = """policy-options {
            prefix-list TEST1-NETS {
                100.0.0.0/24;
            }
            policy-statement TEST1-NETS {
                term TEST1 {
                    from {
                        prefix-list TEST1-NETS;
                    }
                    then accept;
                }
                term REJECT {
                    then reject;
                }
            }
        }"""
        self.conf.load(textdata, overwrite=True)
        self.assertEqual(mock_exec.call_args[0][0].tag, "load-configuration")
        self.assertEqual(
            mock_exec.call_args[0][0].getchildren()[0].tag, "configuration-text"
        )
        self.assertEqual(
            mock_exec.call_args[0][0].attrib, {"format": "text", "action": "override"}
        )

    def _read_file(self, fname):
        fpath = os.path.join(os.path.dirname(__file__), "rpc-reply", fname)
        foo = open(fpath).read()

        # specific to multi rpc error
        if fname == "commit-configuration.xml":
            raw = etree.XML(foo)
            obj = RPCReply(raw)
            obj.parse()
            raise RPCError(etree.XML(foo), errs=obj._errors)

    def _mock_manager(self, *args, **kwargs):
        if kwargs:
            device_params = kwargs["device_params"]
            device_handler = make_device_handler(device_params)
            session = SSHSession(device_handler)
            return Manager(session, device_handler)

        elif args:
            return self._read_file(args[0].tag + ".xml")
