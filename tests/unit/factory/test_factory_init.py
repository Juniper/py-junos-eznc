import unittest
from unittest.mock import mock_open, patch

import yaml

from jnpr.junos.factory import loadyaml


class TestFactoryInit(unittest.TestCase):
    @patch("jnpr.junos.factory.FactoryLoader")
    @patch("jnpr.junos.factory.yaml.load")
    @patch("jnpr.junos.factory.open", new_callable=mock_open, read_data="---\nA: {}\n")
    def test_loadyaml_uses_yaml_safeloader(
        self, mock_file, mock_yaml_load, mock_loader
    ):
        mock_yaml_load.return_value = {}
        mock_loader.return_value.load.return_value = {}

        loadyaml("dummy.yml")

        self.assertEqual(mock_yaml_load.call_args.kwargs["Loader"], yaml.SafeLoader)


if __name__ == "__main__":
    unittest.main()
