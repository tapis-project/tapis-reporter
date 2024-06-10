import logging
import os
import re
from datetime import datetime, time, timedelta
from time import sleep

import django
import requests
import splunklib.client as client
import splunklib.results as results

logger = logging.getLogger(__name__)

os.environ["DJANGO_SETTINGS_MODULE"] = "reporter.settings"
django.setup()

from ..apps.tapis.models import Paper


def save_tapis_papers(tapis_papers):
    """
    Add tapis papers to database

    :return: Bool -- True or False
    """
    try:
        Paper.objects.bulk_create(tapis_papers)
        return True
    except Exception as e:
        logger.error(f"Unable to add tapis papers; error: {e}")
        return False


def get_tapis_papers():
    papers_url = requests.get(
        "https://raw.githubusercontent.com/tapis-project/tapis-reporting/main/tapis_papers.json"
    )
    papers_data = papers_url.json()

    logger.debug(f"papers_data: {papers_data}")

    status = save_tapis_papers(papers_data)
    return status


def query_splunk(
    host: str,
    port: int,
    username: str,
    password: str,
    scheme: str,
    search: str,
    test: bool,
    regex: str,
) -> list[dict]:
    """
    This function is used to query splunk and return a dict of results

    Args:
        host (str): Where the Splunk instance lives
        port (int): The port of the Splunk instance
        username (str): Username to authenticate with
        password (str): Password to authenticate with
        scheme (str): http or https of Splunk instance
        search (str): Base 64 encoded string of search query

    Returns:
        splunk_data (list[dict]): list of dictionaries containing data that matches Splunk regex schema

    """
    try:
        splunk_service = client.connect(
            host=host,
            port=port,
            username=username,
            password=password,
            scheme=scheme,
        )
    except Exception as e:
        raise Exception(f"Error connecting to Splunk: {e}")

    end_date = datetime.combine(datetime.today(), time.min)
    start_date = end_date - timedelta(days=1)
    temp_date = start_date

    hours = []
    while temp_date <= end_date:
        hours.append(temp_date)
        temp_date += timedelta(hours=1)

    try:
        total_result_count = 0
        splunk_data = []
        for _ in range(len(hours) - 1):
            search_query = search + f" earliest={start_date} AND latest={end_date}"

            search_results = splunk_service.jobs.create(search_query)

            while not search_results.is_done():
                sleep(0.2)

            result_count = int(search_results["resultCount"])

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

                                nginx_log_format = re.compile(rf"{regex}")

                                log_data = re.match(nginx_log_format, log)

                                if log_data:
                                    if test:
                                        return {
                                            "resultCount": result_count,
                                            "sampleResult": log_data.groupdict(),
                                            "error": None,
                                        }
                                    splunk_data.append(log_data.groupdict())

                        except Exception as e:
                            logger.debug(f"Error parsing log: {e}")
                            logger.debug(result["_raw"])
    except Exception as e:
        logger.error(f"Ran into error somewhere retrieving data -- error: {e}")
        return e

    return splunk_data
