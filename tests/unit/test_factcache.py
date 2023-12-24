try:
    import unittest2 as unittest
except ImportError:
    import unittest
import nose2
from mock import patch, MagicMock, call
from jnpr.junos.exception import FactLoopError

from jnpr.junos import Device

from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession

__author__ = "Stacy Smith"
__credits__ = "Jeremy Schulman, Nitin Kumar"


class TestFactCache(unittest.TestCase):
    @patch("ncclient.manager.connect")
    def setUp(self, mock_connect):
        mock_connect.side_effect = self._mock_manager_setup
        self.dev = Device(host="1.1.1.1", user="rick", password="password123")
        self.dev.open()

    def test_factcache_unknown_fact(self):
        with self.assertRaises(KeyError):
            unknown = self.dev.facts["unknown"]

    def test_factcache_fact_loop(self):
        # The personality fact calls the
        # model fact.
        # Change the callback for the model
        # fact to be the same as the personality fact
        # in order to induce a fact loop.
        self.dev.facts._callbacks["model"] = self.dev.facts._callbacks["personality"]
        # Now, trying to fetch the personality
        # fact should cause a FactLoopError
        with self.assertRaises(FactLoopError):
            personality = self.dev.facts["personality"]

    def test_factcache_return_unexpected_fact(self):
        # Create a callback for the foo fact.
        self.dev.facts._callbacks["foo"] = get_foo_bar_fact
        # Now, trying to access the foo fact should cause a
        # RunTimeError because the bar fact is also unexpectedly provided
        with self.assertRaises(RuntimeError):
            foo = self.dev.facts["foo"]

    @patch("jnpr.junos.factcache.warnings")
    def test_factcache_nonmatching_old_and_new_fact(self, mock_warn):
        # Set fact style to 'both'
        self.dev._fact_style = "both"
        # Create a callback for the foo fact.
        self.dev.facts._callbacks["foo"] = get_foo_fact
        # Cache the new-style foo fact
        self.dev.facts._cache["foo"] = "foo"
        # Set the old-style foo fact to a different value
        self.dev._ofacts["foo"] = "bar"
        # Now, trying to access the foo fact should cause a
        # RunTimeWarning because the values of the new and old-style facts
        # do not match
        foo = self.dev.facts["foo"]
        mock_warn.assert_has_calls(
            [
                call.warn(
                    "New and old-style facts do not match for the foo fact.\n"
                    "    New-style value: foo\n    Old-style value: bar\n",
                    RuntimeWarning,
                )
            ]
        )

    def test_factcache_fail_to_return_expected_fact(self):
        # Create a callback for the foo fact.
        self.dev.facts._callbacks["foo"] = get_bar_fact
        self.dev.facts._callbacks["bar"] = get_bar_fact
        # Now, trying to access the foo fact should cause a
        # RunTimeError because the foo fact is not provided
        with self.assertRaises(RuntimeError):
            foo = self.dev.facts["foo"]

    def test_factcache_delete_fact(self):
        # Create a callback for the foo fact.
        self.dev.facts._callbacks["foo"] = get_foo_fact
        foo = self.dev.facts["foo"]
        # Now, trying to delete the foo fact should cause a
        # RunTimeError
        with self.assertRaises(RuntimeError):
            self.dev.facts.pop("foo", None)

    def test_factcache_set_fact(self):
        # Create a callback for the foo fact.
        self.dev.facts._callbacks["foo"] = get_foo_fact
        foo = self.dev.facts["foo"]
        # Now, trying to set the foo fact should cause a
        # RunTimeError
        with self.assertRaises(RuntimeError):
            self.dev.facts["foo"] = "bar"

    def test_factcache_iter_facts(self):
        # Override the callbacks
        self.dev.facts._callbacks = {
            "foo": get_foo_fact,
            "bar": get_bar_fact,
            "_hidden": get_foo_bar_fact,
        }
        # Now, get the length of the facts
        self.assertEqual(len(list(self.dev.facts)), 2)

    def test_factcache_len_facts(self):
        # Override the callbacks
        self.dev.facts._callbacks = {"foo": get_foo_fact, "bar": get_bar_fact}
        # Now, get the length of the facts
        self.assertEqual(len(self.dev.facts), 2)

    def test_factcache_string_repr(self):
        # Override the callbacks to only support foo and bar facts.
        self.dev.facts._callbacks = {"foo": get_foo_fact, "bar": get_bar_fact}
        # Set values for foo and bar facts
        self.dev.facts._cache["foo"] = "foo"
        self.dev.facts._cache["bar"] = {"bar": "bar"}
        # Now, get the string (pretty) representation of the facts
        self.assertEqual(
            str(self.dev.facts), "{'bar': {'bar': 'bar'}, " "'foo': 'foo'}"
        )

    def test_factcache_repr_facts(self):
        # Override the callbacks
        self.dev.facts._callbacks = {"foo": get_foo_fact, "bar": get_bar_fact}
        # Now, get the length of the facts
        self.assertEqual(str(self.dev.facts), "{'bar': 'bar', 'foo': 'foo'}")

    def test_factcache_refresh_single_key(self):
        # Override the callbacks
        self.dev.facts._callbacks = {
            "foo": get_foo_fact,
            "bar": get_bar_fact,
            "_hidden": get_hidden_fact,
        }
        # Populate the cache
        self.dev.facts._cache["foo"] = "before"
        self.dev.facts._cache["bar"] = "before"
        self.dev.facts._cache["_hidden"] = "before"
        # Confirm the cached values
        self.assertEqual(self.dev.facts["foo"], "before")
        self.assertEqual(self.dev.facts["bar"], "before")
        self.assertEqual(self.dev.facts["_hidden"], "before")
        # Refresh just the foo fact
        self.dev.facts._refresh(keys="foo")
        # Confirm the values now
        self.assertEqual(self.dev.facts["foo"], "foo")
        self.assertEqual(self.dev.facts["bar"], "before")
        self.assertEqual(self.dev.facts["_hidden"], "before")

    def test_factcache_refresh_two_keys(self):
        # Override the callbacks
        self.dev.facts._callbacks = {
            "foo": get_foo_fact,
            "bar": get_bar_fact,
            "_hidden": get_hidden_fact,
        }
        # Populate the cache
        self.dev.facts._cache["foo"] = "before"
        self.dev.facts._cache["bar"] = "before"
        self.dev.facts._cache["_hidden"] = "before"
        # Confirm the cached values
        self.assertEqual(self.dev.facts["foo"], "before")
        self.assertEqual(self.dev.facts["bar"], "before")
        self.assertEqual(self.dev.facts["_hidden"], "before")
        # Refresh the foo and _hidden facts
        self.dev.facts._refresh(keys=("foo", "_hidden"))
        # Confirm the values now
        self.assertEqual(self.dev.facts["foo"], "foo")
        self.assertEqual(self.dev.facts["bar"], "before")
        self.assertEqual(self.dev.facts["_hidden"], True)

    def test_factcache_refresh_unknown_fact(self):
        # Override the callbacks
        self.dev.facts._callbacks = {"foo": get_foo_fact, "_hidden": get_hidden_fact}
        # Populate the cache
        self.dev.facts._cache["foo"] = "before"
        self.dev.facts._cache["_hidden"] = "before"
        # Confirm the cached values
        self.assertEqual(self.dev.facts["foo"], "before")
        self.assertEqual(self.dev.facts["_hidden"], "before")
        # Refresh just the unknown bar fact which should raise a RuntimeError
        with self.assertRaises(RuntimeError):
            self.dev.facts._refresh(keys=("bar"))

    def test_factcache_refresh_all_facts(self):
        # Override the callbacks
        self.dev.facts._callbacks = {
            "foo": get_foo_fact,
            "bar": get_bar_fact,
            "_hidden": get_hidden_fact,
        }
        # Populate the cache
        self.dev.facts._cache["foo"] = "before"
        self.dev.facts._cache["bar"] = "before"
        self.dev.facts._cache["_hidden"] = "before"
        # Confirm the cached values
        self.assertEqual(self.dev.facts["foo"], "before")
        self.assertEqual(self.dev.facts["bar"], "before")
        self.assertEqual(self.dev.facts["_hidden"], "before")
        # Refresh all facts
        self.dev.facts._refresh()
        # Confirm the values now
        self.assertEqual(self.dev.facts["foo"], "foo")
        self.assertEqual(self.dev.facts["bar"], "bar")
        self.assertEqual(self.dev.facts["_hidden"], True)

    @patch("jnpr.junos.device.warnings")
    def test_factcache_refresh_exception_on_failure(self, mock_warn):
        # Override the callbacks
        self.dev.facts._callbacks = {
            "foo": get_foo_raise_error,
        }
        # Populate the cache
        self.dev.facts._cache["foo"] = "before"
        # Confirm the cached values
        self.assertEqual(self.dev.facts["foo"], "before")
        with self.assertRaises(ValueError):
            self.dev.facts._refresh(exception_on_failure=True, keys="foo")

    @patch("jnpr.junos.device.warnings")
    def test_factcache_refresh_no_exception_on_failure(self, mock_warn):
        # Override the callbacks
        self.dev.facts._callbacks = {
            "foo": get_foo_raise_error,
        }
        # Populate the cache
        self.dev.facts._cache["foo"] = "before"
        # Confirm the cached values
        self.assertEqual(self.dev.facts["foo"], "before")
        self.dev.facts._refresh(exception_on_failure=False, keys="foo")
        self.assertEqual(self.dev.facts["foo"], None)

    @patch("jnpr.junos.device.warnings")
    @patch("jnpr.junos.factcache.warnings")
    def test_factcache_refresh_warnings_on_failure(self, mock_warn, mock_device_warn):
        # Refresh all facts with warnings on failure
        self.dev.facts._refresh(warnings_on_failure=True)
        mock_warn.assert_has_calls(
            [
                call.warn(
                    "Facts gathering is incomplete. To know the reason call "
                    '"dev.facts_refresh(exception_on_failure=True)"',
                    RuntimeWarning,
                )
            ]
        )
        # mock_warn.assert_called_once('Facts gathering is incomplete. '
        #                              'To know the reason call '
        #                              '"dev.facts_refresh('
        #                              'exception_on_failure=True)"',
        #                              RuntimeWarning)

    def _mock_manager_setup(self, *args, **kwargs):
        if kwargs:
            device_params = kwargs["device_params"]
            device_handler = make_device_handler(device_params)
            session = SSHSession(device_handler)
            return Manager(session, device_handler)


def get_foo_fact(device):
    return {"foo": "foo"}


def get_foo_bar_fact(device):
    return {
        "foo": "foo",
        "bar": "bar",
    }


def get_bar_fact(device):
    return {
        "bar": "bar",
    }


def get_hidden_fact(device):
    return {
        "_hidden": True,
    }


def get_foo_raise_error(device):
    raise ValueError("Error")
