try:
    import unittest2 as unittest
except ImportError:
    import unittest
import nose2

from lxml.etree import XML

from jnpr.junos.device import Device
from jnpr.junos.utils.config import Config
from jnpr.junos.exception import RpcError, ConfigLoadError
from jnpr.junos.decorators import timeoutDecorator, normalizeDecorator
from jnpr.junos.decorators import ignoreWarnDecorator

from mock import patch, MagicMock, PropertyMock, call

from ncclient.operations.rpc import RPCError
from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession
from ncclient.xml_ import qualify

__author__ = "Rick Sherman"


class Test_Decorators(unittest.TestCase):
    @patch("ncclient.manager.connect")
    def setUp(self, mock_connect):
        mock_connect.side_effect = self._mock_manager_setup
        self.dev = Device(
            host="1.1.1.1", user="rick", password="password123", gather_facts=False
        )
        self.dev.open()

    def test_timeout(self):
        with patch(
            "jnpr.junos.Device.timeout", new_callable=PropertyMock
        ) as mock_timeout:
            mock_timeout.return_value = 30

            def function(x):
                return x

            decorator = timeoutDecorator(function)
            decorator(self.dev, dev_timeout=10)
            calls = [call(), call(10), call(30)]
            mock_timeout.assert_has_calls(calls)

    def test_timeout_except(self):
        with patch(
            "jnpr.junos.Device.timeout", new_callable=PropertyMock
        ) as mock_timeout:
            mock_timeout.return_value = 30

            def function(*args, **kwargs):
                raise Exception()

            decorator = timeoutDecorator(function)
            # test to ensure the exception is raised
            with self.assertRaises(Exception):
                decorator(self.dev, dev_timeout=10)
            calls = [call(), call(10), call(30)]
            # verify timeout was set/reset
            mock_timeout.assert_has_calls(calls)

    # Test default of true and passing true keyword
    def test_normalize_true_true(self):
        with patch(
            "jnpr.junos.Device.transform", new_callable=PropertyMock
        ) as mock_transform:
            self.dev._normalize = True

            def function(x):
                return x

            decorator = normalizeDecorator(function)
            decorator(self.dev, normalize=True)
            self.assertFalse(mock_transform.called)

    # Test default of true and passing true keyword and a func exception
    def test_normalize_true_true_except(self):
        with patch(
            "jnpr.junos.Device.transform", new_callable=PropertyMock
        ) as mock_transform:
            self.dev._normalize = True

            def function(*args, **kwargs):
                raise Exception()

            decorator = normalizeDecorator(function)
            with self.assertRaises(Exception):
                decorator(self.dev, normalize=True)
            self.assertFalse(mock_transform.called)

    # Test default of True and passing false keyword
    def test_normalize_true_false(self):
        with patch(
            "jnpr.junos.Device.transform", new_callable=PropertyMock
        ) as mock_transform:
            mock_transform.return_value = "o.g."
            self.dev._normalize = True

            def function(x):
                return x

            decorator = normalizeDecorator(function)
            decorator(self.dev, normalize=False)
            calls = [call(), call(self.dev._nc_transform), call("o.g.")]
            mock_transform.assert_has_calls(calls)

    # Test default of True and passing false keyword and a func exception
    def test_normalize_true_false_except(self):
        with patch(
            "jnpr.junos.Device.transform", new_callable=PropertyMock
        ) as mock_transform:
            mock_transform.return_value = "o.g."
            self.dev._normalize = True

            def function(*args, **kwargs):
                raise Exception()

            decorator = normalizeDecorator(function)
            with self.assertRaises(Exception):
                decorator(self.dev, normalize=False)
            calls = [call(), call(self.dev._nc_transform), call("o.g.")]
            mock_transform.assert_has_calls(calls)

    # Test default of false and passing true keyword
    def test_normalize_false_true(self):
        with patch(
            "jnpr.junos.Device.transform", new_callable=PropertyMock
        ) as mock_transform:
            mock_transform.return_value = "o.g."
            self.dev._normalize = False

            def function(x):
                return x

            decorator = normalizeDecorator(function)
            decorator(self.dev, normalize=True)
            calls = [call(), call(self.dev._norm_transform), call("o.g.")]
            # print mock_transform.call_args_list
            mock_transform.assert_has_calls(calls)

    # Test default of false and passing true keyword and a func exception
    def test_normalize_false_true_except(self):
        with patch(
            "jnpr.junos.Device.transform", new_callable=PropertyMock
        ) as mock_transform:
            mock_transform.return_value = "o.g."
            self.dev._normalize = False

            def function(*args, **kwargs):
                raise Exception()

            decorator = normalizeDecorator(function)
            with self.assertRaises(Exception):
                decorator(self.dev, normalize=True)
            calls = [call(), call(self.dev._norm_transform), call("o.g.")]
            # print mock_transform.call_args_list
            mock_transform.assert_has_calls(calls)

    # Test default of false and passing false keyword
    def test_normalize_false_false(self):
        with patch(
            "jnpr.junos.Device.transform", new_callable=PropertyMock
        ) as mock_transform:
            self.dev._normalize = False

            def function(x):
                return x

            decorator = normalizeDecorator(function)
            decorator(self.dev, normalize=False)
            self.assertFalse(mock_transform.called)

    # Test default with ignore_warning not present.
    def test_ignore_warning_missing(self):
        def method(self, x):
            return x

        decorator = ignoreWarnDecorator(method)
        response = decorator(self.dev, "foo")
        self.assertEqual("foo", response)

    # Test default with ignore_warning=False.
    def test_ignore_warning_false(self):
        def method(self, x):
            return x

        decorator = ignoreWarnDecorator(method)
        response = decorator(self.dev, "foo", ignore_warning=False)
        self.assertEqual("foo", response)

    # Test with ignore_warning=True and only warnings.
    def test_ignore_warning_true_3snf_warnings(self):
        self.dev._conn.rpc = MagicMock(side_effect=self._mock_manager_3snf_warnings)
        cu = Config(self.dev)
        config = """
            delete interfaces ge-0/0/0
            delete protocols ospf
            delete policy-options prefix-list foo
        """
        self.assertTrue(cu.load(config, ignore_warning=True))

    # Test with ignore_warning='statement not found' and 3 snf warnings.
    def test_ignore_warning_string_3snf_warnings(self):
        self.dev._conn.rpc = MagicMock(side_effect=self._mock_manager_3snf_warnings)
        cu = Config(self.dev)
        config = """
            delete interfaces ge-0/0/0
            delete protocols ospf
            delete policy-options prefix-list foo
        """
        self.assertTrue(cu.load(config, ignore_warning="statement not found"))

    # Test with ignore_warning='statement not found', 1 snf warning,
    # and 1 error.
    def test_ignore_warning_string_1snf_warning_1err(self):
        self.dev._conn.rpc = MagicMock(side_effect=self._mock_manager_1snf_warning_1err)
        cu = Config(self.dev)
        config = """
            delete interfaces ge-0/0/0
            delete protcols ospf
            delete policy-options prefix-list foo
        """
        with self.assertRaises(ConfigLoadError):
            cu.load(config, ignore_warning="statement not found")

    # Test with ignore_warning=True, RpcError with no errs attribute.
    # I haven't seen this from an actual device, so this is a very contrived
    # test.
    def test_ignore_warning_string_1snf_warning_1err(self):
        def method(self, x):
            rpc_error = RPCError(XML("<foo/>"), errs=None)
            raise rpc_error

        decorator = ignoreWarnDecorator(method)
        with self.assertRaises(RPCError):
            decorator(self.dev, "foo", ignore_warning=True)

    # Test with ignore_warning=['foo', 'statement not found'] and
    # three statement not found warnings.
    def test_ignore_warning_list_3snf_warnings(self):
        self.dev._conn.rpc = MagicMock(side_effect=self._mock_manager_3snf_warnings)
        cu = Config(self.dev)
        config = """
            delete interfaces ge-0/0/0
            delete protocols ospf
            delete policy-options prefix-list foo
        """
        self.assertTrue(cu.load(config, ignore_warning=["foo", "statement not found"]))

    # Test with ignore_warning='foo', and three statement not found warnings.
    def test_ignore_warning_string_3snf_no_match(self):
        self.dev._conn.rpc = MagicMock(side_effect=self._mock_manager_3snf_warnings)
        cu = Config(self.dev)
        config = """
            delete interfaces ge-0/0/0
            delete protcols ospf
            delete policy-options prefix-list foo
        """
        with self.assertRaises(ConfigLoadError):
            cu.load(config, ignore_warning="foo")

    # Test with ignore_warning=['foo', 'bar], and
    # three statement not found warnings.
    def test_ignore_warning_list_3snf_no_match(self):
        self.dev._conn.rpc = MagicMock(side_effect=self._mock_manager_3snf_warnings)
        cu = Config(self.dev)
        config = """
            delete interfaces ge-0/0/0
            delete protcols ospf
            delete policy-options prefix-list foo
        """
        with self.assertRaises(ConfigLoadError):
            cu.load(config, ignore_warning=["foo", "bar"])

    # Test with ignore_warning=['foo', 'bar], and
    # three warnings which are 'foo boom', 'boom bar', and 'foo bar'
    def test_ignore_warning_list_3warn_match(self):
        self.dev._conn.rpc = MagicMock(side_effect=self._mock_manager_3foobar_warnings)
        cu = Config(self.dev)
        config = """
            delete interfaces ge-0/0/0
            delete protcols ospf
            delete policy-options prefix-list foo
        """
        self.assertTrue(cu.load(config, ignore_warning=["foo", "bar"]))

    # Test with ignore_warning=['foo', 'foo bar], and
    # three warnings which are 'foo boom', 'boom bar', and 'foo bar'
    def test_ignore_warning_list_3warn_no_match(self):
        self.dev._conn.rpc = MagicMock(side_effect=self._mock_manager_3foobar_warnings)
        cu = Config(self.dev)
        config = """
            delete interfaces ge-0/0/0
            delete protcols ospf
            delete policy-options prefix-list foo
        """
        with self.assertRaises(ConfigLoadError):
            cu.load(config, ignore_warning=["foo", "foo bar"])

    def _mock_manager_setup(self, *args, **kwargs):
        if kwargs:
            device_params = kwargs["device_params"]
            device_handler = make_device_handler(device_params)
            session = SSHSession(device_handler)
            return Manager(session, device_handler)

    def _mock_manager_3snf_warnings(self, *args, **kwargs):
        cmd = """
        <load-configuration action="set" format="text">
            <configuration-set>
                delete interfaces ge-0/0/0
                delete protocols ospf
                delete policy-options prefix-list foo
            </configuration-set>
        </load-configuration>
        """
        rsp_string = """
<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" xmlns:junos="http://xml.juniper.net/junos/16.1R4/junos" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="urn:uuid:1f3dfa00-3434-414a-8aa8-0073590c5812">
<load-configuration-results>
<rpc-error>
<error-severity>warning</error-severity>
<error-message>
statement not found
</error-message>
</rpc-error>
<rpc-error>
<error-severity>warning</error-severity>
<error-message>
statement not found
</error-message>
</rpc-error>
<rpc-error>
<error-severity>warning</error-severity>
<error-message>
statement not found
</error-message>
</rpc-error>
<ok/>
</load-configuration-results>
</rpc-reply>
        """
        rsp = XML(rsp_string)
        errors = []
        for err in rsp.findall(".//" + qualify("rpc-error")):
            errors.append(RPCError(err))
        raise RPCError(rsp, errs=errors)

    def _mock_manager_3foobar_warnings(self, *args, **kwargs):
        cmd = """
        <load-configuration action="set" format="text">
            <configuration-set>
                delete interfaces ge-0/0/0
                delete protocols ospf
                delete policy-options prefix-list foo
            </configuration-set>
        </load-configuration>
        """
        rsp_string = """
        <rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" xmlns:junos="http://xml.juniper.net/junos/16.1R4/junos" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="urn:uuid:1f3dfa00-3434-414a-8aa8-0073590c5812">
            <load-configuration-results>
                <rpc-error>
                    <error-severity>warning</error-severity>
                    <error-message>
                        foo boom
                    </error-message>
                </rpc-error>
                <rpc-error>
                    <error-severity>warning</error-severity>
                    <error-message>
                        boom bar
                    </error-message>
                </rpc-error>
                <rpc-error>
                    <error-severity>warning</error-severity>
                    <error-message>
                        foo bar
                    </error-message>
                </rpc-error>
                <ok/>
            </load-configuration-results>
        </rpc-reply>
        """
        rsp = XML(rsp_string)
        errors = []
        for err in rsp.findall(".//" + qualify("rpc-error")):
            errors.append(RPCError(err))
        raise RPCError(rsp, errs=errors)

    def _mock_manager_1snf_warning_1err(self, *args, **kwargs):
        cmd = """
        <load-configuration action="set" format="text">
            <configuration-set>
                delete interfaces ge-0/0/0
                delete protcols ospf
                delete policy-options prefix-list foo
            </configuration-set>
        </load-configuration>
        """
        rsp_string = """
        <rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" xmlns:junos="http://xml.juniper.net/junos/16.1R4/junos" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="urn:uuid:1f3dfa00-3434-414a-8aa8-0073590c5812">
            <load-configuration-results>
                <rpc-error>
                    <error-severity>warning</error-severity>
                    <error-message>
                    statement not found
                    </error-message>
                </rpc-error>
                <rpc-error>
                    <error-type>protocol</error-type>
                    <error-tag>operation-failed</error-tag>
                    <error-severity>error</error-severity>
                    <error-message>syntax error</error-message>
                    <error-info>
                    <bad-element>protcols</bad-element>
                    </error-info>
                </rpc-error>
                <ok/>
            </load-configuration-results>
        </rpc-reply>
        """
        rsp = XML(rsp_string)
        errors = []
        for err in rsp.findall(".//" + qualify("rpc-error")):
            errors.append(RPCError(err))
        raise RPCError(rsp, errs=errors)
