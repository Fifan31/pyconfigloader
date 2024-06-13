# -*- coding: utf-8 -*-
"""PyConfigLoader."""

import logging
import os
from pathlib import Path
from typing import Callable, Generator, Mapping, Optional, Union  # noqa: F401

from appdirs import AppDirs

__author__ = "Stéphan AIMÉ"
__email__ = "stephan.aime@gmail.com"
__version__ = "0.2.0"

from dynaconf import Dynaconf

logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger(__name__)

SUPPORTED_EXT = sorted([".json", ".yml", ".yaml", ".ini", ".properties", ".toml", ".env"])


class ConfigurationError(Exception):
    """
    Exception class for Configuration
    """


class Configuration(Dynaconf):
    """
    Configuration class that gather all configuration items retrieved from common config file
    locations.

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
        self.load_file(file_path)

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
