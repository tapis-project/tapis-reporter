import os
import django
import logging

os.environ["DJANGO_SETTINGS_MODULE"] = "reporter.settings"
django.setup()

from reporter.apps.tapis.models import TapisInfo, JobsData

logger = logging.getLogger(__name__)


class Populate:
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

    def populate(self):
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
        vars_with_vals = {
            "avg_daily_jobs": 0,
            "dev_daily_jobs": 0,
            "total_jobs": 0,
            "num_using_smart_scheduling": 0
        }
        with open(file, "rt") as outfile:
            for line in outfile:
                values = line.strip()
                try:
                    if len(values) > 1:
                        values_list = values.split(" ")
                        vars_with_vals["avg_daily_jobs"] = values_list[0]
                        vars_with_vals["dev_daily_jobs"] = values_list[2],
                        vars_with_vals["total_jobs"] = values_list[4]
                    elif len(values) == 1:
                        vars_with_vals["num_using_smart_scheduling"] = values
                except Exception as e:
                        logger.error(f"Unable to get jobs data: {e}")

        return vars_with_vals

    def save_jobs_data(self):
        if self.jobs_data:
            new_jobs_data = {
                "avg_daily_jobs": self.jobs_data["avg_daily_jobs"],
                "dev_daily_jobs": self.jobs_data["dev_daily_jobs"],
                "total_jobs": self.jobs_data["total_jobs"],
                "num_using_smart_scheduling": self.jobs_data["num_using_smart_scheduling"]
            }
            JobsData.objects.filter(id=1).update(**new_jobs_data)

    def save_tapis_data(self, total_by_tenant, users_by_tenant):
        if total_by_tenant and users_by_tenant:

            bulk_tapis_info = []
            for tenant in total_by_tenant:
                num_tokens = total_by_tenant[tenant]
                num_unique_users = users_by_tenant[tenant]
                if tenant in self.apps_data:
                    num_ctr_apps = self.apps_data[tenant]
                else:
                    num_ctr_apps = 0

                tenant_info = TapisInfo(
                    tenant=tenant,
                    num_tokens=int(num_tokens),
                    num_unique_users=int(num_unique_users),
                    num_ctr_apps=int(num_ctr_apps),
                )

                bulk_tapis_info.append(tenant_info)

            TapisInfo.objects.bulk_create(bulk_tapis_info, update_conflicts=True)


if __name__ == "__main__":
    populate = Populate()
    populate.populate()
