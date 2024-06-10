from ...bases.API.splunk_plugin_base import SplunkPluginBase


class TapisSplunkPlugin(SplunkPluginBase):
    def parse_query_results(self):
        # results = self.query_splunk()
        # for result in results:
        #     datetimestamp = result["datetimestamp"]
        #     dt_string = datetimestamp[:-6]
        #     dt_microseconds = dt_string.split(".")[1]
        #     dt_string = dt_string.split(".")[0] + "." + dt_microseconds[0:3]

        #     service = result["path"].split("/")[2]
        #     parsed_service = urlparse(service)
        #     service = urlunparse(parsed_service._replace(query=""))

        #     tenant = result["tenant"]

        #     if tenant == "www":
        #         tenant = result["host"].split(".")[1]

        #     tenants_and_services[tenant] = tenants_and_services.get(tenant, {})
        #     tenants_and_services[tenant][service] = (
        #         tenants_and_services[tenant].get(service, 0) + 1
        #     )
        return
