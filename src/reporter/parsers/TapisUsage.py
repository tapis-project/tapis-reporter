import os
from datetime import datetime, time, timedelta
import django
import logging
from django.conf import settings
import json
import re
import requests
from time import sleep
from urllib.parse import urlparse, urlunparse

import splunklib.client as client
import splunklib.results as results

os.environ["DJANGO_SETTINGS_MODULE"] = "reporter.settings"
django.setup()

from ..apps.services.tapis.models import TenantServiceUsage

logger = logging.getLogger(__name__)


class TapisUsage:

    def __init__(self):
        self.slack_channel = settings.SLACK_CHANNEL
        self.slack_username = settings.SLACK_USER
        self.slack_url = settings.SLACK_URL

    def query_splunk(self):
        splunk_service = client.connect(
            host=settings.SPLUNK_HOST,
            port=settings.SPLUNK_PORT,
            username=settings.SPLUNK_USER,
            password=settings.SPLUNK_PASS,
            scheme="https")
        
        midnight = datetime.combine(datetime.today(), time.min)
        yesterday_midnight = midnight - timedelta(days=1)
        start_time = yesterday_midnight

        hours = []
        while start_time <= midnight:
            hours.append(start_time)
            start_time += timedelta(hours=1)

        bulk_splunk_data = []
        tenants_and_services = {}
        total_result_count = 0

        for i in range(len(hours)-1):
            current_timestamp = hours[i]
            next_timestamp = hours[i+1]

            start_time = current_timestamp.strftime("%H:%M:%S")
            end_time = next_timestamp.strftime("%H:%M:%S")
            earliest = current_timestamp.strftime("%m/%d/%Y:%H:%M:%S")
            latest = next_timestamp.strftime("%m/%d/%Y:%H:%M:%S")

            current_month = current_timestamp.month
            current_day = current_timestamp.day
            current_year = current_timestamp.year

            search_query = f"search index=kube_events namespace=tapis-prod \
                container_name=tapis-nginx NOT Gatus NOT healthcheck \
                earliest={earliest} AND latest={latest} AND tapis_version=v3"
            
            search_results = splunk_service.jobs.create(search_query)

            while not search_results.is_done():
                sleep(.2)
            
            result_count = int(search_results["resultCount"])

            if result_count > 0:
                total_result_count += result_count
                offset = 0
                count = 50000

                while (offset < result_count):
                    kwargs_paginate = {
                        "count": count,
                        "offset": offset,
                        "output_mode": 'json'
                    }

                    block_results = search_results.results(**kwargs_paginate)

                    for result in results.JSONResultsReader(block_results):
                        try:
                            if isinstance(result, dict):
                                log = result["_raw"]

                                nginx_log_format = re.compile(
                                    r'(?P<tap_datetimestamp>[\d\-:T\.+]+) \S+ \S+ (?P<tap_client_ip>\d+\.\d+\.\d+\.\d+) - - \[(?P<tap_date>\d{2}/\w+/\d{4}):(?P<tap_time>\d{2}:\d{2}:\d{2}) (\+|\-)\d{4}\] "(?P<tap_host>(?P<tap_tenant>.*?)\.\S+)" "(?P<tap_request_method>\S+) (?P<tap_path>\S+) \S+" (?P<tap_status_code>\d+) (?P<tap_bytes_sent>\d+) "(?P<tap_referer>[^"]*)" "(?P<tap_user_agent>[^"]*)" "-"'
                                )

                                log_data = re.match(nginx_log_format, log)

                                if log_data:
                                    data_dict = log_data.groupdict()

                                    datetimestamp = data_dict['tap_datetimestamp']
                                    dt_string = datetimestamp[:-6]
                                    dt_microseconds = dt_string.split('.')[1]
                                    dt_string = dt_string.split('.')[0] + '.' + dt_microseconds[0:3]
                                    datetime_object = datetime.fromisoformat(dt_string)
                                    timestamp = datetime_object.timestamp()

                                    tap_service = data_dict['tap_path'].split('/')[2]
                                    parsed_service = urlparse(tap_service)
                                    tap_service = urlunparse(parsed_service._replace(query=''))

                                    tenant = data_dict['tap_tenant']

                                    if tenant == 'www':
                                        tenant = data_dict['tap_host'].split('.')[1]

                                    tenants_and_services[tenant] = tenants_and_services.get(tenant, {})
                                    tenants_and_services[tenant][tap_service] = tenants_and_services[tenant].get(tap_service, 0) + 1
                        except Exception as e:
                            logger.error(f"Error parsing log: {e}")
                            logger.error(result["_raw"])
                            nginx_log_format = re.compile(
                                r'(?P<tap_datetimestamp>[\d\-:T\.+]+) \S+ \S+ (?P<tap_client_ip>\d+\.\d+\.\d+\.\d+) - - \[(?P<tap_date>\d{2}/\w+/\d{4}):(?P<tap_time>\d{2}:\d{2}:\d{2}) (\+|\-)\d{4}\] "(?P<tap_host>(?P<tap_tenant>.*?)\.\S+)" "(?P<tap_request_method>\S+) (?P<tap_path>\S+) \S+" (?P<tap_status_code>\d+) (?P<tap_bytes_sent>\d+) "(?P<tap_referer>[^"]*)" "(?P<tap_user_agent>[^"]*)" "-"'
                            )
                            
                            log_data = re.match(nginx_log_format, log)
                            logger.error(log_data)
                    
                    offset += count
                
                for tenant in tenants_and_services:
                    for service in tenants_and_services[tenant]:
                        splunk_data = TenantServiceUsage(
                            log_day=current_day,
                            log_month=current_month,
                            log_year=current_year,
                            start_time=start_time,
                            end_time=end_time,
                            tenant=tenant,
                            service=service,
                            log_count=tenants_and_services[tenant][service]
                        )
                        bulk_splunk_data.append(splunk_data)

                logger.debug(tenants_and_services)
                tenants_and_services = {}

        saved = False
        try:
            TenantServiceUsage.objects.bulk_create(bulk_splunk_data)
            saved = True
        except Exception as e:
            logger.error(f"Unable to save splunk data; error: {e}")

        message = f"Got {total_result_count} TAPIS NGNINX logs from Splunk API call for {yesterday_midnight} - {midnight}"

        if not saved:
            message += " -- Got error saving info!"

        self.message_slack(message)

    def message_slack(self, message):
        data = {'channel': self.slack_channel, 'username': self.slack_username}
        data['text'] = message

        try:
            requests.post(self.slack_url, data=json.dumps(data))
        except Exception as e:
            logger.error(f"Unable to message Slack: {e}")
