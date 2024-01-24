import os
import django
import logging

os.environ["DJANGO_SETTINGS_MODULE"] = "reporter.settings"
django.setup()

from reporter.apps.services.tapis.models import TapisInfo, TenantInfo, JobsData

logger = logging.getLogger(__name__)


class Populate:
    """
    Handles data from tapis servers to save info from database calls

    """

    def __init__(self):
        self.file_dir = self.get_file_dir()

    @classmethod
    def get_file_dir(self):
        data_path = "/app/reporter/dbdata/"
        return data_path

    def populate(self):
        files_to_parse = os.listdir(self.file_dir) if self.file_dir != "" else []
        if self.file_dir != "":
            if self.file_dir[-1] == "/":
                self.file_dir = self.file_dir[:-1]
            for i in range(len(files_to_parse)):
                files_to_parse[i] = self.file_dir + "/" + files_to_parse[i]

        apps_data = {}
        total_by_tenant = {}
        users_by_tenant = {}
        jobs_data = {}
        for file in files_to_parse:
            filename = os.path.basename(file)
            # Num ctr apps
            if "apps" in filename:
                apps_data = self.parse_apps_out(file)
            # Num tokens, num unique users
            elif "auth" in filename:
                total_by_tenant, users_by_tenant = self.parse_auth_out(file)
            # JobsData
            elif "jobs" in filename:
                jobs_data = self.parse_jobs_out(file)
            else:
                logger.debug(f"Skipping file: {file}")

        if apps_data and total_by_tenant and users_by_tenant and jobs_data:
            total_num_tokens = 0
            total_num_unique_users = 0
            total_num_ctr_apps = 0

            avg_daily_jobs = jobs_data["avg_daily_jobs"]
            dev_daily_jobs = jobs_data["dev_daily_jobs"]
            total_jobs = jobs_data["total_jobs"]

            bulk_tenant_info = []
            for tenant in total_by_tenant:
                total_num_tokens = total_num_tokens + int(total_by_tenant[tenant])
                total_num_unique_users = total_num_unique_users + int(
                    users_by_tenant[tenant]
                )
                num_tokens = total_by_tenant[tenant]
                num_unique_users = users_by_tenant[tenant]
                if tenant in apps_data:
                    total_num_ctr_apps = total_num_ctr_apps + int(apps_data[tenant])
                    num_ctr_apps = apps_data[tenant]
                else:
                    num_ctr_apps = 0

                tenant_info = TenantInfo(
                    tenant=tenant,
                    num_tokens=int(num_tokens),
                    num_unique_users=int(num_unique_users),
                    num_ctr_apps=int(num_ctr_apps),
                )

                bulk_tenant_info.append(tenant_info)

            tapis_info = TapisInfo(
                num_tokens=total_num_tokens,
                num_unique_users=total_num_unique_users,
                num_ctr_apps=total_num_ctr_apps,
            )
            tapis_info.save()

            TenantInfo.objects.bulk_create(bulk_tenant_info, update_conflicts=True)

            jobs_data = JobsData(
                avg_daily_jobs=avg_daily_jobs,
                dev_daily_jobs=dev_daily_jobs,
                total_jobs=total_jobs,
            )
            jobs_data.save()

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
        with open(file, "rt") as outfile:
            for line in outfile:
                values = line.strip()
                values_list = values.split(" ")
                vars_with_vals = {
                    "avg_daily_jobs": values_list[0],
                    "dev_daily_jobs": values_list[2],
                    "total_jobs": values_list[4],
                }

        return vars_with_vals


if __name__ == "__main__":
    populate = Populate()
    populate.populate()
