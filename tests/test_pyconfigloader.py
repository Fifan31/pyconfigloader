import contextlib
import io
import os
import tempfile
import textwrap
import unittest

from pyconfigloader import Configuration, ConfigurationError, _dict_merge

test_ini = textwrap.dedent(
    """
    [SECTION1]
    key1 = value1
    key2 = value2

    [DEV]
    server = server de dev

    [PROD]
    server = prod server pas touche
"""
).strip()

test_ini_output = {
    "SECTION1": {"key1": "value1", "key2": "value2"},
    "DEV": {"server": "server de dev"},
    "PROD": {"server": "prod server pas touche"},
}

test_json = textwrap.dedent(
    """
    {
        "SETTING3": "x",
        "SETTING4": [1, 2],
        "SETTING5": {"foo": "bar"},
        "SETTING_SOURCE": "json",
        "NON_ASCII": "ইঈউঊঋঌ"
    }
"""
).strip()

test_json_output = {
    "SETTING3": "x",
    "SETTING4": [1, 2],
    "SETTING5": {"foo": "bar"},
    "SETTING_SOURCE": "json",
    "NON_ASCII": "ইঈউঊঋঌ",
}

test_yaml = textwrap.dedent(
    """
    SETTING1: x
    SETTING2:
      - 1
      - 2
    SETTING_SOURCE: yaml
    SETTING3:
      foo: bar
    NON_ASCII: ইঈউঊঋঌ
"""
).strip()

test_yaml_output = {
    "SETTING1": "x",
    "SETTING2": [1, 2],
    "SETTING_SOURCE": "yaml",
    "SETTING3": {"foo": "bar"},
    "NON_ASCII": "ইঈউঊঋঌ",
}

test_properties = textwrap.dedent(
    """
    SECTION1.key1=value1
    SECTION1.key2=value2

    DEV.server=server de dev

    PROD.server=prod server pas touche
"""
).strip()

test_properties_output = {
    "SECTION1": {"key1": "value1", "key2": "value2"},
    "DEV": {"server": "server de dev"},
    "PROD": {"server": "prod server pas touche"},
}


@contextlib.contextmanager
def temp_config_file(test_data, extension=None):
    with tempfile.NamedTemporaryFile("wb", suffix=extension) as configfile:
        configfile.write(test_data.encode("utf-8"))
        configfile.seek(0)
        yield configfile.name


class TestConfigLoader(unittest.TestCase):
    def setUp(self):
        self.config = Configuration()

    def test_init(self):
        config = Configuration(logger=1)
        assert config["logger"] == 1

    def _test_update_from_file(self, content, method, expected_result, suffix=None):
        with temp_config_file(content, suffix) as test_file_name:
            method(test_file_name)
        assert self.config == expected_result

    def _test_update_from_file_obj(self, content, method, expected_result):
        method(io.StringIO(content))
        assert self.config == expected_result

    # @skip_if_yaml_not_available
    def test_update_from_yaml_file(self):
        self._test_update_from_file(test_yaml, self.config.update_from_yaml_file, test_yaml_output)

    # @skip_if_yaml_not_available
    def test_update_from_yaml_file_obj(self):
        self._test_update_from_file_obj(test_yaml, self.config.update_from_yaml_file, test_yaml_output)

    def test_update_from_ini_file(self):
        self._test_update_from_file(test_ini, self.config.update_from_ini_file, test_ini_output)

    def test_update_from_ini_file_obj(self):
        self._test_update_from_file_obj(test_ini, self.config.update_from_ini_file, test_ini_output)

    def test_update_from_json_file(self):
        self._test_update_from_file(test_json, self.config.update_from_json_file, test_json_output)

    def test_update_from_json_file_obj(self):
        self._test_update_from_file_obj(test_json, self.config.update_from_json_file, test_json_output)

    def test_update_from_properties_file(self):
        self._test_update_from_file(
            test_properties,
            self.config.update_from_properties_file,
            test_properties_output,
        )

    def test_update_from_file_json(self):
        self._test_update_from_file(test_json, self.config.update_from_file, test_json_output, suffix=".json")

    def test_update_from_file_yaml(self):
        self._test_update_from_file(test_yaml, self.config.update_from_file, test_yaml_output, suffix=".yml")

    def test_update_from_file_ini(self):
        self._test_update_from_file(test_ini, self.config.update_from_file, test_ini_output, suffix=".ini")

    def test_update_from_file_properties(self):
        self._test_update_from_file(
            test_properties,
            self.config.update_from_file,
            test_properties_output,
            suffix=".properties",
        )

    def test_load_config_least_important_file(self):
        with temp_config_file(test_json, ".json") as test_file_name:
            self.config.load_config(least_important_files=[test_file_name])
        assert self.config == test_json_output

    def test_load_config_most_important_file(self):
        with temp_config_file(test_json, ".json") as test_file_name:
            self.config.load_config(most_important_files=[test_file_name])
        assert self.config == test_json_output

    def test_load_config_least_important_files(self):
        with temp_config_file(test_json, ".json") as test_file1_name, temp_config_file(
            test_yaml, ".yaml"
        ) as test_file2_name:
            self.config.load_config(least_important_files=[test_file1_name, test_file2_name])
        expected = test_json_output.copy()
        _dict_merge(expected, test_yaml_output)
        self.assertDictEqual(self.config, expected)

    def test_load_config_most_important_files(self):
        with temp_config_file(test_json, ".json") as test_file1_name, temp_config_file(
            test_yaml, ".yaml"
        ) as test_file2_name:
            self.config.load_config(most_important_files=[test_file1_name, test_file2_name])
        expected = test_json_output.copy()
        _dict_merge(expected, test_yaml_output)
        self.assertDictEqual(self.config, expected)

    def test_load_config_least_and_most_important_files(self):
        with temp_config_file(test_json, ".json") as test_file1_name, temp_config_file(
            test_yaml, ".yaml"
        ) as test_file2_name:
            self.config.load_config(
                least_important_files=[test_file1_name],
                most_important_files=[test_file2_name],
            )
        expected = test_json_output.copy()
        _dict_merge(expected, test_yaml_output)
        self.assertDictEqual(self.config, expected)

    def test_load_config_least_and_most_important_files_inversed(self):
        with temp_config_file(test_json, ".json") as test_file1_name, temp_config_file(
            test_yaml, ".yaml"
        ) as test_file2_name:
            self.config.load_config(
                least_important_files=[test_file2_name],
                most_important_files=[test_file1_name],
            )
        expected = test_yaml_output.copy()
        _dict_merge(expected, test_json_output)
        self.assertDictEqual(self.config, expected)

    def test_load_config_least_important_dir(self):
        with temp_config_file(test_json, ".json") as test_file_name:
            self.config.load_config(
                app_name=os.path.splitext(os.path.basename(test_file_name))[0],
                least_important_dirs=[os.path.dirname(test_file_name)],
            )
        self.assertDictEqual(self.config, test_json_output)

    def test_config_eq(self):
        conf_1 = Configuration(a=1, b=2)
        conf_2 = Configuration(a=1, b=2)
        conf_3 = Configuration(a=1, c=3)
        self.assertTrue(conf_1 == conf_2)
        self.assertFalse(conf_1 == conf_3)

    def test_repr(self):
        actual = repr(Configuration(a=1, b=2))
        expected = "Configuration({'a': 1, 'b': 2})"
        self.assertEqual(expected, actual)

    def test_namespace(self):
        config = Configuration(
            MY_APP_SETTING1="a",
            EXTERNAL_LIB_SETTING1="b",
            EXTERNAL_LIB_SETTING2="c",
        )
        actual = config.namespace("EXTERNAL_LIB")
        expected = Configuration({"SETTING1": "b", "SETTING2": "c"})

        self.assertEqual(expected, actual)

    def test_namespace_lower(self):
        config = Configuration(
            MY_APP_SETTING1="a",
            EXTERNAL_LIB_SETTING1="b",
            EXTERNAL_LIB_SETTING2="c",
        )
        actual = config.namespace_lower("EXTERNAL_LIB")
        expected = Configuration({"setting1": "b", "setting2": "c"})

        self.assertEqual(expected, actual)

    def test_sub_configuration_nominal(self):
        config = Configuration()
        config.update_from_json_file(
            io.StringIO(
                textwrap.dedent(
                    """
        {
            "KEY1": "val1",
            "KEY2": {"SUBKEY": "subval"}
        }
        """
                )
            )
        )
        actual = config.sub_configuration("KEY2")
        expected = Configuration()
        expected.update_from_json_file(
            io.StringIO(
                textwrap.dedent(
                    """
        {
            "SUBKEY": "subval"
        }
        """
                )
            )
        )
        self.assertEqual(expected, actual)

    def test_sub_configuration_namespace(self):
        config = Configuration()
        config.update_from_json_file(
            io.StringIO(
                textwrap.dedent(
                    """
        {
            "KEY1": "val1",
            "KEY2": {"SUBKEY": "subval"}
        }
        """
                )
            )
        )
        actual = config.sub_configuration("KEY")
        expected = Configuration()
        expected.update_from_json_file(
            io.StringIO(
                textwrap.dedent(
                    """
                {
                    "1": "val1",
                    "2": {"SUBKEY": "subval"}
                }
                """
                )
            )
        )
        self.assertEqual(expected, actual)

    def test_sub_configuration_error_simple_value(self):
        config = Configuration()
        config.update_from_json_file(
            io.StringIO(
                textwrap.dedent(
                    """
        {
            "KEY1": "val1",
            "KEY2": {"SUBKEY": "subval"}
        }
        """
                )
            )
        )
        self.assertRaises(ConfigurationError, config.sub_configuration, "KEY1")

    def test_sub_configuration_error_unknwown_key(self):
        config = Configuration()
        config.update_from_json_file(
            io.StringIO(
                textwrap.dedent(
                    """
        {
            "KEY1": "val1",
            "KEY2": {"SUBKEY": "subval"}
        }
        """
                )
            )
        )
        actual = config.sub_configuration("Unknown")
        expected = Configuration([])
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
