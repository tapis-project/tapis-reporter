import logging
import os
import re
from abc import ABC, abstractmethod
from datetime import datetime, time, timedelta
from time import sleep

import django
import splunklib.client as client
import splunklib.results as results

os.environ["DJANGO_SETTINGS_MODULE"] = "reporter.settings"
django.setup()

logger = logging.getLogger(__name__)


class SplunkPluginBase(ABC):
    """
    SplunkSource handles connections and data retrieval from Splunk

    Args:
        host (str): Where the Splunk instance lives
        port (int): The port of the Splunk instance
        username (str): Username to authenticate with
        password (str): Password to authenticate with
        scheme (str): http or https of Splunk instance
        search (str): Base 64 encoded string of search query
        format (str):
    """

    def __init__(self, **kwargs):
        try:
            self.validate_kwargs(kwargs)
        except TypeError as e:
            print(e)
            return e

        self.host = kwargs["host"]
        self.port = kwargs["port"]
        self.username = kwargs["username"]
        self.password = kwargs["password"]
        self.scheme = kwargs["scheme"]
        self.search = kwargs["search"]
        self.format = kwargs["format"]

    def validate_kwargs(self, kwargs):
        """
        This function is used to filter out any unwanted kwarg arguments and to check the type of each kwarg

        Raises
        ------
        TypeError:
            Error raised if keyword doesn't exist or type does not match expected type
        """
        allowed_kwargs = {
            "host": str,
            "port": int,
            "username": str,
            "password": str,
            "scheme": str,
            "search": str,
            "format": str,
        }

        for key in kwargs:
            if key not in allowed_kwargs:
                raise TypeError(f"Got unexpected keyword argument: {key}")
            value = kwargs[key]
            exp_type = allowed_kwargs[key]

            if value is not None and not isinstance(value, exp_type):
                raise TypeError(
                    f"Expected {key} to be {exp_type.__name__}, got {type(kwargs[key]).__name__}"
                )

    def test_query(self) -> dict:
        """
        This function is used to test the connection to the Splunk instance

        Returns:
            A dict containing result count and a sample result
        """
        try:
            result = self.query_splunk(test=True)

            return {
                "result_count": result["result_count"],
                "sample_result": result["sample_result"],
            }
        except Exception as e:
            logger.debug(e)
            return e

    def query_splunk(self, test: bool = False) -> list[dict]:
        """
        This function is used to query Splunk and return a dict of results.
        If the test flag is True, will return a list only containing the first result.

        Returns:
            A list of dictionaries portraying logs that match Splunk regex schema
        """
        try:
            splunk_service = client.connect(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                scheme=self.scheme,
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
            splunk_data = []
            for _ in range(len(hours) - 1):
                search_query = (
                    self.search + f" earliest={start_date} AND latest={end_date}"
                )

                search_results = splunk_service.jobs.create(search_query)

                while not search_results.is_done():
                    sleep(0.2)

                result_count = int(search_results["resultCount"])

                if result_count > 0:
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

                                    log_format = re.compile(rf"{self.format}")

                                    log_data = re.match(log_format, log)

                                    if log_data:
                                        if test:
                                            return [log_data.groupdict()]

                                        splunk_data.append(log_data.groupdict())

                            except Exception as e:
                                logger.debug(f"Error parsing log: {e}")
                                logger.debug(result["_raw"])
        except Exception as e:
            logger.error(f"Ran into error somewhere retrieving data -- error: {e}")
            return e

        return splunk_data

    @abstractmethod
    def parse_query_results(self):
        """
        Class responsible for handling parsing of data. Sub classes must implement

        Raises
        ------
        NotImplementedError:
            Error is raised if function is not implemented in subclass
        """
        raise NotImplementedError
