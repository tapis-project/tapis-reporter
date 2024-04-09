import os

import datetime as date
import matplotlib.pyplot as plt
import pathlib
import django
import logging
from django.conf import settings
import requests
from datetime import datetime
import mysql.connector

from itertools import chain

logger = logging.getLogger(__name__)

os.environ["DJANGO_SETTINGS_MODULE"] = "reporter.settings"
django.setup()

from ..apps.jupyterhub.models import FileLog, LoginLog


def generate_email_data(service, tenant, week_begin, week_end) -> dict:
    """
    Given a service, tenant, and date range, return set of data for email

    :param service: Name of service
    :param tenant: Name of tenant
    :param week_begin: Start of week for date range
    :param week_end: End of week for date range
    :return: Dict with data
    """
    proper_name = tenant.proper_name
    tenant_recipients = get_tenant_recipients(tenant)

    match service.name:
        case 'jupyterhub':
            accessed_files = FileLog.objects.filter(tenant=tenant.name, date__range=(week_begin, week_end))
            directories, counts = get_directories_and_counts(service, tenant, accessed_files.values('filepath'))
            plot_path = create_graph(directories, counts)
            jupyterhub_stats = generate_stats(service, tenant, accessed_files, week_begin, week_end)
            # old_servers = get_old_servers()
            data = {
                'tenant_recipients': tenant_recipients,
                'primary_receiver': tenant.primary_receiver,
                'proper_name': proper_name,
                'plot_path': plot_path,
                'jupyterhub_stats': jupyterhub_stats,
                # 'old_servers': old_servers,
                'service': service.name
            }
            return data
        case 'tapis':
            jobs_data = get_jobs_data(week_begin, week_end)
            jobs_data["tenant_recipients"] = tenant_recipients
            jobs_data["primary_receiver"] = tenant.primary_receiver
            return jobs_data
        case _:
            pass


def get_directories_and_counts(service, tenant, accessed_files):
    match service.name:
        case 'jupyterhub':
            filepaths = list(accessed_files)
            dir_counts = {}
            directories = get_tenant_directories(tenant)

            for path in filepaths:
                dir = path['filepath']
                for d in directories:
                    if d in dir:
                        dir_counts[d] = dir_counts.get(d, 0) + 1

            directories = []
            counts = []
            for dir in dir_counts.keys():
                directories.append(dir)
                counts.append(dir_counts[dir])

            counts, directories = zip(*sorted(zip(counts, directories)))

            directories = list(directories)
            counts = list(counts)
            directories.reverse()
            counts.reverse()

            return directories, counts
        case 'tapis':
            pass
        case _:
            pass


def get_tenant_directories(tenant) -> list:
    temp_directories = tenant.tenantdirectory_set.all().values('directory')
    tenant_directories = []

    for dir in list(temp_directories):
        tenant_directories.append(dir['directory'])

    return tenant_directories


def get_tenant_recipients(tenant) -> list:
    temp_recipients = tenant.tenantrecipient_set.all().values('recipient')
    tenant_recipients = []

    for rec in list(temp_recipients):
        tenant_recipients.append(rec['recipient'])

    return tenant_recipients


def create_graph(directories, counts) -> str:
    plt.bar(directories, counts, color='green')
    plt.title('File Access - Notebook Data Depot Locations', fontsize=14)
    plt.xlabel('Directory', fontsize=14)
    plt.ylabel('Count', fontsize=14)
    plt.grid(True)

    filename = str(date.date.today()) + ".png"
    dir = pathlib.Path(__file__).parent.absolute()

    folder = r"/results"

    plot_path = str(dir) + folder + filename

    plt.savefig(plot_path)

    return plot_path


def generate_stats(service, tenant, accessed_files, week_begin, week_end):
    match service.name:
        case 'jupyterhub':
            created_files = accessed_files.filter(action='created')
            opened_files = accessed_files.filter(action='opened')

            num_created_files = created_files.count()
            num_opened_files = opened_files.count()

            login_users = LoginLog.objects.filter(tenant=tenant.name, date__range=(week_begin, week_end))
            unique_login_count = login_users.values('user').distinct().count()
            total_login_count = login_users.count()

            try:
                combined = list(chain(accessed_files, login_users))
                users = []
                for log in combined:
                    users.append(log.user)
                unique_users = set(users)
                unique_user_count = len(unique_users)
            except Exception:
                unique_user_count = 'Error getting unique user count'

            jupyterhub_stats = {
                'num_created_files': num_created_files,
                'num_opened_files': num_opened_files,
                'unique_login_count': unique_login_count,
                'total_login_count': total_login_count,
                'unique_user_count': unique_user_count
            }
            return jupyterhub_stats
        case 'tapis':
            pass
        case _:
            pass


def get_old_servers():
    api_url = settings.JUPYTERHUB_API_URL + '/hub/api/users'
    headers = {
        'Authorization': 'token %s' % settings.JUPYTERHUB_TOKEN
    }

    response = requests.get(api_url, params=None, headers=headers).json()
    last_activity = [{'user': user['name'], 'last_activity': user['last_activity']} for user in response]
    old_servers = []

    for entry in last_activity:
        if entry['last_activity'] is not None:
            last_datestamp = datetime.strptime(entry['last_activity'], "%Y-%m-%dT%H:%M:%S.%f%z")
            last_dt = last_datestamp.replace(tzinfo=None)
            now = datetime.now()

            diff = now - last_dt
            days = diff.days

            if days > 7:
                old_servers.append({'user': entry['user'], 'days': days})

    return old_servers


def get_jobs_data(week_begin, week_end):
    dbdata_path = "/app/reporter/dbdata/tapis"
    dbdata_files = os.listdir(dbdata_path)

    jobs_data = {}

    try:
        mydb = mysql.connector.connect(
            host=settings.MYSQL_HOST,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASS,
            database=settings.MYSQL_DB
        )

        mycursor = mydb.cursor()

        mycursor.execute(f"SELECT tenant_id, count(*) FROM aloe_jobs WHERE accepted between '{week_begin}' AND '{week_end}' group by tenant_id;")

        myresult = mycursor.fetchall()

        v2_jobs_data = {}
        for res in myresult:
            if res[0] is not None:
                v2_jobs_data[res[0]] = res[1]

        jobs_data["v2"] = v2_jobs_data
    except Exception as e:
        logger.error(f"Error getting v2 jobs data: {e}")

    for file in dbdata_files:
        filename = os.path.basename(file)
        filepath = os.path.join(dbdata_path, file)

        if "email-data" in filename:
            try:
                v3_jobs_data = {}

                with open(filepath, "rt") as datafile:
                    data = datafile.read().strip()
                    data = data.split(' ')
                    for i in range(len(data)):
                        if i % 3 == 0:
                            group = data[i]
                            count = data[i + 2]
                            v3_jobs_data[group] = count

                jobs_data["v3"] = v3_jobs_data
            except Exception as e:
                logger.error(f"Error getting v3 jobs data: {e}")
        else:
            continue

    return jobs_data
