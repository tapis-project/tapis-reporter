from .plugin_loader import APIPluginLoader


class SplunkService:
    def __init__(self, plugin_directory: str):
        self.plugin_loader = APIPluginLoader(plugin_directory)
        self.plugin_loader.load_plugins()

    def execute_query(self, query: str):
        results = []
        for plugin in self.plugin_loader.get_plugins():
            result = plugin.query_splunk(query)
            results.append(result)

        return results
