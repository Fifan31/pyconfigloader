# -*- coding: utf-8 -*-
"""PyConfigLoader."""

import configparser
import json
import logging
import os
from pathlib import Path
from typing import Callable, Generator, Mapping, Optional, Union  # noqa: F401

import attrdictionary
from appdirs import AppDirs

__author__ = "Stéphan AIMÉ"
__email__ = "stephan.aime@gmail.com"
__version__ = "0.2.0"

# TODO Replace the following import by a plugin mechanism
try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
try:
    import toml

    TOML_AVAILABLE = True
except ImportError:
    TOML_AVAILABLE = False
try:
    from jproperties import Properties, PropertyTuple

    JPROPERTIES_AVAILABLE = True
except ImportError:
    JPROPERTIES_AVAILABLE = False

logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger(__name__)

SUPPORTED_EXT = sorted([".json", ".yml", ".yaml", ".ini", ".properties", ".toml", ".env"])


class ConfigurationError(Exception):
    """
    Exception class for Configuration
    """


class Configuration(attrdictionary.AttrDict):
    """
    Configuration class that gather all configuration items retrieved from common config file
    locations.

    If `AttrDict`_ is installed, then elements can be accessed as both keys
    and attributes.

    .. _AttrDict: https://github.com/bcj/AttrDict
    """

    # @formatter:off
    # fmt: off
    def load_config(# noqa: PLR0912, PLR0913
        self,  # noqa: ANN101
        app_name: Optional[str] = None,
        app_version: Optional[str] = None,
        least_important_dirs: Optional[list[Union[str, Path]]] = None,
        most_important_dirs: Optional[list[Union[str, Path]]] = None,
        least_important_files: Optional[list[Union[str, Path]]] = None,
        most_important_files: Optional[list[Union[str, Path]]] = None, ) -> None:
        # fmt: off
        # @formatter:on
        """
                        Load a configuration from given and default files from given and default directories
                        :param app_name: Name of the application for which the configuration is loaded
                        :param app_version: Version of the application for which the configuration is loaded
                        :param least_important_dirs: List of directories in which configuration files are searched
                        :param most_important_dirs: List of directories in which configuration files are searched
                        :param least_important_files: List of configuration files to load
                        :param most_important_files: List of configuration files to load
                        """
        least_important_dirs = least_important_dirs or []
        most_important_dirs = most_important_dirs or []
        least_important_files = least_important_files or []
        most_important_files = most_important_files or []

        for cfg_file_full_name in least_important_files:
            self.update_from_file(cfg_file_full_name)

        if app_name:
            for least_important_dir in least_important_dirs:
                for ext in SUPPORTED_EXT:
                    cfg_file_full_name = os.path.join(least_important_dir, f"{app_name}{ext}")
                    if os.path.exists(cfg_file_full_name):
                        self.update_from_file(cfg_file_full_name)

            app_dirs = AppDirs(app_name, version=app_version, multipath=True)
            for cfg_dir in [*app_dirs.site_config_dir.split(os.pathsep), os.path.join("/etc", app_name), ]:
                for ext in SUPPORTED_EXT:
                    cfg_file_full_name = os.path.join(cfg_dir, f"{app_name}{ext}")
                    if os.path.exists(cfg_file_full_name):
                        self.update_from_file(cfg_file_full_name)

            cfg_dir = app_dirs.user_config_dir
            for ext in SUPPORTED_EXT:
                cfg_file_full_name = os.path.join(cfg_dir, f"{app_name}{ext}")
                if os.path.exists(cfg_file_full_name):
                    self.update_from_file(cfg_file_full_name)

            for most_important_dir in most_important_dirs:
                for ext in SUPPORTED_EXT:
                    cfg_file_full_name = os.path.join(most_important_dir, f"{app_name}{ext}")
                    if os.path.exists(cfg_file_full_name):
                        self.update_from_file(cfg_file_full_name)

        for cfg_file_full_name in most_important_files:
            self.update_from_file(cfg_file_full_name)

    def update_from_file(self, file_path: Union[str, Path]) -> None:  # noqa: ANN101
        """
        Updates the current configuration with items held in the given file.
        :param file_path: Path of the configuration file to load
        """
        updater = {".yaml": self.update_from_yaml_file, ".yml": self.update_from_yaml_file,
                   ".json": self.update_from_json_file, ".toml": self.update_from_toml_file,
                   ".ini" : self.update_from_ini_file, ".properties": self.update_from_properties_file, }
        try:
            updater[os.path.splitext(file_path)[1]](file_path)
        except KeyError as err:
            msg = f"Extension of the file '{file_path}' was not recognized."
            raise NotImplementedError(msg) from err

    def update_from_object(self, obj: object, criterion=lambda key: key.isupper()) -> None:  # noqa: ANN001, ANN101
        """
        Update dict from the attributes of a module, class or other object.

        By default only attributes with all-uppercase names will be retrieved.
        Use the ``criterion`` argument to modify that behaviour.

        :arg obj: Either the actual module/object, or its absolute name, e.g.
            'my_app.settings'.

        :arg criterion: Callable that must return True when passed the name
            of an attribute, if that attribute is to be used.
        :type criterion: :py:class:`function`

        .. versionadded:: 1.0
        """
        LOG.info("Loading config from %s", obj)
        if isinstance(obj, str):
            if "." in obj:
                path, name = obj.rsplit(".", 1)
                mod = __import__(path, globals(), locals(), [name], 0)
                obj = getattr(mod, name)
            else:
                obj = __import__(obj, globals(), locals(), [], 0)
        _dict_merge(self, {key: getattr(obj, key) for key in filter(criterion, dir(obj))})

    def update_from_yaml_env(self, env_var):
        """
        Update dict from the YAML file specified in an environment variable.

        The `PyYAML`_ package must be installed before this method can be used.

        :arg env_var: Environment variable name.
        :type env_var: :py:class:`str`

        .. _PyYAML: http://pyyaml.org/wiki/PyYAML
        """
        _check_yaml_module()
        return self._update_from_env(env_var, yaml.safe_load)

    def update_from_yaml_file(self, file_path_or_obj):
        """
        Update dict from a YAML file.

        The `PyYAML`_ package must be installed before this method can be used.

        :arg file_path_or_obj: Filepath or file-like object.

        .. _PyYAML: http://pyyaml.org/wiki/PyYAML
        """
        _check_yaml_module()
        return self._update_from_file(file_path_or_obj, yaml.safe_load)

    def update_from_json_env(self, env_var):
        """
        Update dict from the JSON file specified in an environment variable.

        :arg env_var: Environment variable name.
        :type env_var: :py:class:`str`
        """
        return self._update_from_env(env_var, json.load)

    def update_from_json_file(self, file_path_or_obj):
        """
        Update dict from a JSON file.

        :arg file_path_or_obj: Filepath or file-like object.
        """
        return self._update_from_file(file_path_or_obj, json.load)

    def update_from_toml_file(self, file_path_or_obj):
        """
        Update dict from a TOML file.

        :arg file_path_or_obj: Filepath or file-like object.
        """
        _check_toml_module()
        return self._update_from_file(file_path_or_obj, toml.load)

    def update_from_ini_file(self, file_path_or_obj):
        """
        Update dict from a INI file.

        :arg file_path_or_obj: Filepath or file-like object.
        """

        def ini_loader_as_dict(file_path):  # noqa: ANN001, ANN202
            config = configparser.ConfigParser()
            config.read_file(file_path)
            return attrdictionary.AttrDict(config._sections)

        return self._update_from_file(file_path_or_obj, ini_loader_as_dict)

    def update_from_properties_file(self, file_path_or_obj):
        """
        Update dict from a PROPERTIES file.

        :arg file_path_or_obj: Filepath or file-like object.
        """

        def properties_loader_as_dict(file_path):  # noqa: ANN001, ANN202
            properties = Properties()
            with open(file_path, "rb") as cfg_file:
                properties.load(cfg_file, "utf-8")
            # change composite key as 'a.b.c=v' to dict '{a:{b:{c:v}}}'
            rv: dict = {}
            for k in properties.properties:
                val = properties[k]
                tmp: dict = {}
                for subkey in k.split(".")[::-1]:
                    tmp: dict = {subkey: val}
                    val = tmp
                _dict_merge(rv, tmp)
            return rv

        _check_jproperties_module()
        _dict_merge(
            self, properties_loader_as_dict(file_path_or_obj)
        )  # return self.update(properties_loader_as_dict(file_path_or_obj))

    def update_from_env_namespace(self, namespace):
        """
        Update dict from any environment variables that have a given prefix.

        The common prefix is removed when converting the variable names to
        dictionary keys. For example, if the following environment variables
        were set::

            MY_APP_SETTING1=foo
            MY_APP_SETTING2=bar

        Then calling ``.update_from_env_namespace('MY_APP')`` would be
        equivalent to calling
        ``.update({'SETTING1': 'foo', 'SETTING2': 'bar'})``.

        :arg namespace: Common environment variable prefix.
        :type env_var: :py:class:`str`
        """
        _dict_merge(
            self, Configuration(os.environ).namespace(namespace)
        )  # self.update(Configuration(os.environ).namespace(namespace))

    def sub_configuration(self, namespace: str) -> "Configuration":  # noqa: ANN101
        """
        Return a subset of the current configuration. Only items with parent 'namespace'
        are returned
        :param namespace:
        :return:
        """
        sub = self.get(namespace)
        if sub is None:
            rv = self.namespace(namespace)
        elif isinstance(sub, str):
            msg = f"Can't extract sub configuration for namespace {namespace}"
            raise ConfigurationError(msg)
        elif isinstance(sub, dict):
            rv = sub

        return rv

    def namespace(self, namespace, key_transform=lambda key: key):
        """
        Return a copy with only the keys from a given namespace.

        The common prefix will be removed in the returned dict. Example::

            >>> from pyconfigloader import Configuration
            >>> config = Configuration(
            ...     MY_APP_SETTING1='a',
            ...     EXTERNAL_LIB_SETTING1='b',
            ...     EXTERNAL_LIB_SETTING2='c',
            ... )
            >>> config.namespace('EXTERNAL_LIB')
            Configuration({'SETTING1': 'b', 'SETTING2': 'c'})

        :arg namespace: Common prefix.
        :arg key_transform: Function through which to pass each key when
            creating the new dictionary.

        :return: New config dict.
        :rtype: :class:`ConfigLoader`
        """
        namespace = namespace.rstrip("_")
        rv = [(key_transform(key[len(namespace):]).lstrip("_"), value) for key, value in self.items() if
              key[: len(namespace)] == namespace]
        return Configuration(rv)

    def namespace_lower(self, namespace):
        """
        Return a copy with only the keys from a given namespace, lower-cased.

        The keys in the returned dict will be transformed to lower case after
        filtering, so they can be easily passed as keyword arguments to other
        functions. This is just syntactic sugar for calling
        :meth:`~ConfigLoader.namespace` with
        ``key_transform=lambda key: key.lower()``.

        Example::

            >>> from pyconfigloader import Configuration
            >>> config = Configuration(
            ...     MY_APP_SETTING1='a',
            ...     EXTERNAL_LIB_SETTING1='b',
            ...     EXTERNAL_LIB_SETTING2='c',
            ... )
            >>> config.namespace_lower('EXTERNAL_LIB')
            Configuration({'setting1': 'b', 'setting2': 'c'})

        :arg namespace: Common prefix.

        :return: New config dict.
        :rtype: :class:`ConfigLoader`
        """
        return self.namespace(namespace, key_transform=lambda key: key.lower())

    def _update_from_env(self, env_var, loader):  # noqa: ANN001, ANN101, ANN202
        if env_var in os.environ:
            self._update_from_file_path(os.environ[env_var], loader)
        else:
            LOG.warning("Not loading config from %s; variable not set", env_var)

    def _update_from_file(self, file_path_or_obj, loader):  # noqa: ANN001, ANN101, ANN202
        if hasattr(file_path_or_obj, "read"):
            self._update_from_file_obj(file_path_or_obj, loader)
        else:
            self._update_from_file_path(file_path_or_obj, loader)

    def _update_from_file_path(self, file_path, loader):  # noqa: ANN001, ANN101, ANN202
        if os.path.exists(file_path):
            with open(file_path) as file_obj:
                LOG.info("Loading config from path %s", os.path.abspath(file_path))
                self._update_from_file_obj(file_obj, loader)
        else:
            LOG.warning("Not loading config from %s; file not found", file_path)

    def _update_from_file_obj(self, file_obj, loader: Callable) -> None:  # noqa: ANN001, ANN101
        if hasattr(file_obj, "name") and isinstance(file_obj.name, str):
            LOG.info("Loading config from file object %s", os.path.abspath(file_obj.name))
        _dict_merge(self, loader(file_obj))  # self.update(loader(file_obj))

    def __repr__(self) -> str:  # noqa: ANN101
        """Represent as a string."""
        return f"{type(self).__name__}({dict.__repr__(self)})"

    def __eq__(self, other: object) -> bool:  # noqa: ANN101
        if other is self:
            return True
        if isinstance(other, Configuration):
            return self.as_dict() == other.as_dict()
        if isinstance(other, dict):
            return self.as_dict() == other
        return False

    def _as_dict(self, dic: Union[dict, PropertyTuple]) -> dict:  # noqa: ANN101
        if JPROPERTIES_AVAILABLE and isinstance(dic, PropertyTuple):
            return self._as_dict(dic.data)

        if not isinstance(dic, dict):
            return dic

        rv = {}
        for k, v in dic.items():
            rv[k] = self._as_dict(v)
        return rv

    def as_dict(self) -> dict:  # noqa: ANN101
        """
        Return the configuration object as a simple dict

        :return: New dict.
        :rtype: :class:`dict`
        """
        return self._as_dict(self)


def _check_yaml_module() -> None:
    if not YAML_AVAILABLE:
        err = ImportError(
            "yaml module not found; please install PyYAML in order to enable "
            "configuration to be loaded from YAML files",
        )
        err.name = "yaml"
        err.path = __file__
        raise err


def _check_toml_module() -> None:
    if not TOML_AVAILABLE:
        err = ImportError(
            "toml module not found; please install toml in order to enable "
            "configuration to be loaded from TOML files",
        )
        err.name = "toml"
        err.path = __file__
        raise err


def _check_jproperties_module() -> None:
    if not JPROPERTIES_AVAILABLE:
        err = ImportError(
            "jproperties module not found; please install jpropeties in order to enable "
            "configuration to be loaded from PROPERTIES files",
        )
        err.name = "jproperties"
        err.path = __file__
        raise err


def _dict_merge(dct: dict, merge_dct: Union[dict, Mapping]) -> None:
    """Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
    updating only top-level keys, dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
    ``dct``.
    :param dct: dict onto which the merge is executed
    :param merge_dct: dct merged into dct
    :return: None
    """
    for k, v in merge_dct.items():
        if k in dct and isinstance(dct[k], dict) and isinstance(v, Mapping):
            _dict_merge(dct[k], v)
        else:
            dct[k] = v
