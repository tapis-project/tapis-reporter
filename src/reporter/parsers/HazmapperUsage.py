import json
import logging
import os
import re
from datetime import datetime, timedelta
from time import sleep

import django
import requests
import splunklib.client as client
import splunklib.results as results
from django.conf import settings
from elasticsearch import Elasticsearch

os.environ["DJANGO_SETTINGS_MODULE"] = "reporter.settings"
django.setup()

from ..apps.hazmapper.models import HazmapperData

logger = logging.getLogger(__name__)


class HazmapperUsage:
    def __init__(self):
        self.slack_channel = settings.SLACK_CHANNEL
        self.slack_username = settings.SLACK_USER
        self.slack_url = settings.SLACK_URL
        self.elastic_client = self.elastic_search()

    def elastic_search(self, host=settings.ELASTIC_HOST):
        """
        Connects to DesignSafe Elasticsearch
        :param host: str: DesignSafe Elasticsearch host location
        :return: es: Elasticsearch client
        """
        usr = settings.ELASTIC_USR
        pwd = settings.ELASTIC_PWD
        auth = (usr, pwd)
        es = Elasticsearch(host, http_auth=auth, use_ssl=True)

        return es

    def query_splunk(self, args):
        splunk_service = client.connect(
            host=settings.SPLUNK_HOST,
            port=settings.SPLUNK_PORT,
            username=settings.SPLUNK_USER,
            password=settings.SPLUNK_PASS,
            scheme="https",
        )

        end_date = datetime.today().strftime("%m/%d/%Y:%H:%M:%S")
        start_date = (datetime.today() - timedelta(days=1)).strftime(
            "%m/%d/%Y:%H:%M:%S"
        )

        if args.start_date is not None:
            start_date = datetime.strptime(args.start_date, "%m/%d/%Y:%H:%M:%S")
            if args.end_date is not None:
                end_date = datetime.strptime(args.end_date, "%m/%d/%Y:%H:%M:%S")

                if start_date > end_date:
                    logger.error(
                        f"Error querying splunk, start date {start_date} later than end date {end_date}"
                    )
                    return

                start_date = args.start_date
                end_date = args.end_date

        # logger.debug(start_date, end_date)
        # temp_date = start_date

        # hours = []
        # while temp_date <= end_date:
        #     hours.append(temp_date)
        #     temp_date += timedelta(hours=1)

        bulk_splunk_data = []
        total_result_count = 0

        search_query = f'search host="prod.geoapi-services.tacc.utexas.edu" earliest={start_date} AND latest={end_date}'

        search_results = splunk_service.jobs.create(search_query)

        while not search_results.is_done():
            sleep(0.2)

        result_count = int(search_results["resultCount"])

        hazmapper_tracking = {}
        log_entries = []
        if result_count > 0:
            total_result_count += result_count
            offset = 0
            count = 50000

            while offset < result_count:
                kwargs_paginate = {
                    "count": count,
                    "offset": offset,
                    "output_mode": "json",
                }

                block_results = search_results.results(**kwargs_paginate)

                for result in results.JSONResultsReader(block_results):
                    try:
                        if isinstance(result, dict):
                            log = result["_raw"]
                            # Example log: Jun 10 15:08:16 prod.geoapi-services.tacc.utexas.edu geoapi_api[992]: 2024-06-10 20:08:16,443 :: INFO :: [projects.py:315] :: Get features of project for user:uwrapid application:hazmapper public_view:False project_uuid:7073c5aa-3ec8-499d-99ac-11548709a54f project:1022 tapis_system_id:project-7484001337096999406-242ac117-0001-012 tapis_system_path:/#015

                            re_format = "(?P<date>\w{3} .{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<host>\S+) (?P<process>\S+\[\d+\]): (?P<datestamp>\d{4}\-\d{2}\-\d{2}) \S+ :: \S+ :: \[(?P<file>\S+\:\d+)\] :: (?P<action>.*):(?P<user>\S+) \S+:(?P<application>\S+) \S+:(?P<public_view>\S+) \S+:(?P<project_uuid>\S+) \S+:(?P<project>\d+) \S+:(?P<tapis_system_id>\S+) \S+:(?P<tapis_system_path>\S+)"

                            new_log_format = re.compile(rf"{re_format}")
                            if "project_uuid" in log and "Get features" in log:
                                log_data = re.match(new_log_format, log)

                                if log_data:
                                    data_dict = log_data.groupdict()
                                    log_entries.append(data_dict)

                    except Exception as e:
                        print(e)

                offset += count

            for log in log_entries:
                user = log["user"]
                map = log["project_uuid"]
                time = log["time"]

                date = log["datestamp"]
                date_time = datetime.strptime(f"{date}:{time}", "%Y-%m-%d:%H:%M:%S")

                if user in hazmapper_tracking:
                    if map in hazmapper_tracking[user] and (
                        date_time
                        - datetime.strptime(
                            f"{hazmapper_tracking[user][map][-1]['date']}:{hazmapper_tracking[user][map][-1]['time']}",
                            "%Y-%m-%d:%H:%M:%S",
                        )
                        > timedelta(minutes=60)
                    ):
                        hazmapper_tracking[user][map].append(
                            {"date": date, "time": time}
                        )
                        self.add_log(bulk_splunk_data, log)
                    if map not in hazmapper_tracking[user]:
                        hazmapper_tracking[user][map] = []
                        hazmapper_tracking[user][map].append(
                            {"date": date, "time": time}
                        )
                        self.add_log(bulk_splunk_data, log)
                if user not in hazmapper_tracking:
                    hazmapper_tracking[user] = {}
                    hazmapper_tracking[user][map] = []
                    hazmapper_tracking[user][map].append({"date": date, "time": time})
                    self.add_log(bulk_splunk_data, log)

            saved = False
            try:
                HazmapperData.objects.bulk_create(bulk_splunk_data)
                saved = True
            except Exception as e:
                logger.error(f"Unable to save splunk data; error: {e}")

            if args.start_date is not None:
                message = f"Finished parsing splunk logs from {start_date} - {end_date}"
            else:
                message = f"Got {total_result_count} TAPIS NGINX logs from Splunk API call for {start_date} - {end_date}"

            if not saved:
                message += " -- Got error saving info!"

        # self.message_slack(message)

    def message_slack(self, message):
        data = {"channel": self.slack_channel, "username": self.slack_username}
        data["text"] = message

        try:
            requests.post(self.slack_url, data=json.dumps(data))
        except Exception as e:
            logger.error(f"Unable to message Slack: {e}")

    def add_log(self, splunk_data, log):
        user = log["user"]
        time = log["time"]
        date = log["datestamp"]

        map = log["project_uuid"]
        application = log["application"]
        is_public = bool(log["public_view"])
        ds_project = log["tapis_system_id"]

        splunk_data.append(
            HazmapperData(
                user=user,
                date=date,
                time=time,
                map=map,
                application=application,
                is_public=is_public,
                project=ds_project,
                published=self.check_published(ds_project.replace("project-", "")),
            )
        )

    def check_published(self, uuid: str):
        """
        Returns ElasticSearch json of DesignSafe published project metaData. May including versions.
        :param include_versions: bool: True=include versions; False=only base PRJ-#### metadata
        :param remove_dupes: bool: True=if include_versions=False only Keep latest version for projects that have multiple.
        :return:
        """
        es = self.elastic_client
        index = "designsafe-production-publications"
        query = {"match_phrase": {"project.uuid": uuid}}
        resp = es.search(index=index, query=query)
        project_count = resp["hits"]["total"]["value"]
        return project_count > 0
