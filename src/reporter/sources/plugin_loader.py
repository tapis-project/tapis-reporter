import importlib
import os

from .bases.API.splunk_plugin_base import SplunkPluginBase


class APIPluginLoader:
    def __init__(self, plugin_directory: str):
        self.plugin_directory = (
            plugin_directory  # /src/reporter/sources/bases/plugins/API
        )
        self.plugins = {}

    def load_plugins(self):
        for filename in os.listdir(self.plugin_directory):
            if filename.endswith(".py"):
                module_name = filename[:-3]
                module = importlib.import_module(
                    f"{self.plugin_directory}.{module_name}"
                )
                for attr in dir(module):
                    if not attr.startswith("__"):
                        plugin_class = getattr(module, attr)
                        if (
                            issubclass(plugin_class, SplunkPluginBase)
                            and plugin_class is not SplunkPluginBase
                        ):
                            self.plugins.setdefault("splunk_plugins", []).append(
                                plugin_class()
                            )

    def get_plugins(self):
        return self.plugins
