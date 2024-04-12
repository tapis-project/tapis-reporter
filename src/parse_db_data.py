import logging
import os

import django
import pandas as pd

os.environ["DJANGO_SETTINGS_MODULE"] = "reporter.settings"
django.setup()

from reporter.apps.tapis.models import JobsData, TapisInfo, TenantJobsData

logger = logging.getLogger(__name__)


class DBParser:
    """
    Handles data from tapis servers to save info from database calls

    """

    def __init__(self):
        self.file_dir = self.get_file_dir()
        self.apps_data = {}
        self.jobs_data = {}

    @classmethod
    def get_file_dir(self):
        data_path = "/app/reporter/dbdata/tapis"
        return data_path

    def parse_db_files(self):
        files_to_parse = os.listdir(self.file_dir) if self.file_dir != "" else []
        if self.file_dir != "":
            if self.file_dir[-1] == "/":
                self.file_dir = self.file_dir[:-1]
            for i in range(len(files_to_parse)):
                files_to_parse[i] = self.file_dir + "/" + files_to_parse[i]

        total_by_tenant = {}
        users_by_tenant = {}

        for file in files_to_parse:
            filename = os.path.basename(file)
            # Num ctr apps
            if "apps" in filename:
                self.apps_data = self.parse_apps_out(file)

            # Num tokens, num unique users
            elif "auth" in filename:
                total_by_tenant, users_by_tenant = self.parse_auth_out(file)

            # JobsData
            elif "jobs" in filename:
                if "jobs-backlog" in filename:
                    self.save_jobs_backlog(file)
                elif "jobs-query" in filename:
                    self.jobs_data = self.parse_jobs_out(file)

            else:
                logger.debug(f"Skipping file: {file}")

        self.save_jobs_data()
        self.save_tapis_data(total_by_tenant, users_by_tenant)

    def parse_apps_out(self, file):
        with open(file, "rt") as outfile:
            for line in outfile:
                group_string = line.strip()
                group_and_counts = group_string.split(" ")
                group_with_count = {}
                for i in range(len(group_and_counts)):
                    if i % 3 == 0:
                        group = group_and_counts[i]
                        count = group_and_counts[i + 2]
                        group_with_count[group] = count

        return group_with_count

    def parse_auth_out(self, file):
        total_by_tenant = {}
        users_by_tenant = {}
        with open(file, "rt") as outfile:
            for num, line in enumerate(outfile):
                group_string = line.strip()
                group_and_counts = group_string.split(" ")
                for i in range(len(group_and_counts)):
                    if i % 3 == 0:
                        group = group_and_counts[i]
                        count = group_and_counts[i + 2]
                        if num == 0:
                            total_by_tenant[group] = count
                        elif num == 1:
                            users_by_tenant[group] = count

        return total_by_tenant, users_by_tenant

    def parse_jobs_out(self, file):
        # JobsData example object
        # {
        #     "tenant": 'tacc',
        #     "avg_daily_jobs": 10,
        #     "dev_daily_jobs": 3.7,
        #     "total_jobs": 1200,
        #     "num_using_smart_scheduling": 0
        # }
        with open(file, "r") as db_file:
            head = [next(db_file).strip() for _ in range(3)]

        # Generate list of JobsData objects (tenant, avg, dev, total, smart)
        # If there is no tenant set tenant to "tapis"
        # If tenant is "tapis", set smart scheduling, else don't set
        # head will have 3 elements
        # 0 = tapis data
        # 1 = num smart scheduling
        # 2 = tenant data
        jobs_data = []
        tapis_values = head[0].split(" ")
        jobs_data.append(
            {
                "tenant": "tapis",
                "avg_daily_jobs": tapis_values[0],
                "dev_daily_jobs": tapis_values[2],
                "total_jobs": tapis_values[4],
                "num_using_smart_scheduling": head[1],
            }
        )

        raw_tenant_jobs = head[2].split(" ")
        raw_tenant_jobs = [x for x in raw_tenant_jobs if x != "|"]

        tenants_with_jobs = [
            raw_tenant_jobs[n : n + 4] for n in range(0, len(raw_tenant_jobs), 4)
        ]

        tenant_job_objs = [
            {
                "tenant": rec[0],
                "avg_daily_jobs": rec[1],
                "dev_daily_jobs": rec[2],
                "total_jobs": rec[3],
            }
            for rec in tenants_with_jobs
        ]

        jobs_data.extend(tenant_job_objs)

        return jobs_data

    def save_jobs_data(self):
        try:
            for tenant_job_data in self.jobs_data:
                JobsData.objects.update_or_create(**tenant_job_data)
        except Exception as e:
            logger.error(f"Error saving JobsData: {e}")

    def save_jobs_backlog(self, file):
        df = pd.read_csv(
            file,
            usecols=["tenant", "count", "date", "version"],
        )

        df_records = df.to_dict(orient="records")

        try:
            jobs_objects = [TenantJobsData(**record) for record in df_records]

            TenantJobsData.objects.bulk_create(jobs_objects)
        except Exception as e:
            logger.error(f"Error saving jobs: {e}")

    def save_tapis_data(self, total_by_tenant, users_by_tenant):
        if total_by_tenant and users_by_tenant:
            # bulk_tapis_info = []
            for tenant in total_by_tenant:
                num_tokens = total_by_tenant[tenant]
                num_unique_users = users_by_tenant[tenant]
                if tenant in self.apps_data:
                    num_ctr_apps = self.apps_data[tenant]
                else:
                    num_ctr_apps = 0

                tenant_info, created = TapisInfo.objects.update_or_create(
                    tenant=tenant,
                    num_tokens=int(num_tokens),
                    num_unique_users=int(num_unique_users),
                    num_ctr_apps=int(num_ctr_apps),
                )

            # Will only work in updated Django
            # TapisInfo.objects.bulk_create(
            #     bulk_tapis_info,
            #     update_conflicts=True,
            #     unique_fields=["tenant"],
            #     update_fields=["num_tokens", "num_unique_users", "num_ctr_apps"]
            # )


if __name__ == "__main__":
    dbparser = DBParser()
    dbparser.parse_db_files()
