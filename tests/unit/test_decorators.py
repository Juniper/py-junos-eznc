__author__ = "Rick Sherman"

import unittest2 as unittest
from nose.plugins.attrib import attr

from jnpr.junos.device import Device
from jnpr.junos.decorators import timeoutDecorator

from mock import patch, PropertyMock, call

from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession


@attr('unit')
class Test_Decorators(unittest.TestCase):

    @patch('ncclient.manager.connect')
    def setUp(self, mock_connect):
        mock_connect.side_effect = self._mock_manager
        self.dev = Device(host='1.1.1.1', user='rick', password='password123',
                          gather_facts=False)
        self.dev.open()

    def test_timeout(self):
        with patch('jnpr.junos.Device.timeout', new_callable=PropertyMock) as mock_timeout:
            mock_timeout.return_value = 30
            function = lambda x: x
            decorator = timeoutDecorator(function)
            decorator(self.dev, dev_timeout=10)
            calls = [call(), call(10), call(30)]
            mock_timeout.assert_has_calls(calls)

    def test_timeout_except(self):
        with patch('jnpr.junos.Device.timeout', new_callable=PropertyMock) as mock_timeout:
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

    def _mock_manager(self, *args, **kwargs):
        if kwargs:
            device_params = kwargs['device_params']
            device_handler = make_device_handler(device_params)
            session = SSHSession(device_handler)
            return Manager(session, device_handler)
