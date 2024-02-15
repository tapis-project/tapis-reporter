import os
import django
import logging
import pandas as pd

os.environ["DJANGO_SETTINGS_MODULE"] = "reporter.settings"
django.setup()

from reporter.apps.services.tapis.models import TenantServiceUsage

logger = logging.getLogger(__name__)


class ParseSplunkCsv:
    """
    Handles data from tapis servers to save info from database calls

    """

    def __init__(self):
        self.file_dir = self.get_file_dir()

    @classmethod
    def get_file_dir(self):
        data_path = "/app/reporter/splunkdata/tapis"
        return data_path

    def parse_splunk_csv(self):
        files_to_parse = os.listdir(self.file_dir) if self.file_dir != "" else []
        if self.file_dir != "":
            if self.file_dir[-1] == "/":
                self.file_dir = self.file_dir[:-1]
            for i in range(len(files_to_parse)):
                files_to_parse[i] = self.file_dir + "/" + files_to_parse[i]

        for file in files_to_parse:
            try:
                df = pd.read_csv(file, usecols=['log_day', 'log_month', 'log_year', 'start_time', 'end_time', 'tenant', 'service', 'log_count'])
                df = df.drop_duplicates()
                df_records = df.to_dict(orient='records')
                
                splunk_data = [TenantServiceUsage(
                    log_date=f"{record['log_year']}-{record['log_month']}-{record['log_day']}",
                    start_time=record['start_time'],
                    end_time=record['end_time'],
                    tenant=record['tenant'],
                    service=record['service'],
                    log_count=record['log_count']
                ) for record in df_records]

                TenantServiceUsage.objects.bulk_create(splunk_data)
            except Exception as e:
                logger.error(e)


if __name__ == "__main__":
    parser = ParseSplunkCsv()
    parser.parse_splunk_csv()
