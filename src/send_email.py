import os
import sys
import argparse
import django
import smtplib
import datetime as date
import logging
import matplotlib.pyplot as plt
import pathlib
from itertools import chain
from django.conf import settings

from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.message import EmailMessage
from email.mime.base import MIMEBase

logger = logging.getLogger(__name__)

os.environ["DJANGO_SETTINGS_MODULE"] = "reporter.settings"
django.setup()

from reporter.apps.jupyterhub.models import FileLog, LoginLog, Tenant, TenantDirectory, TenantRecipient


host = 'relay.tacc.utexas.edu'
port = 25

parser = argparse.ArgumentParser(description='Process arguments for email')
parser.add_argument('tenant')
args = parser.parse_args()

tenants = Tenant.objects.all().values('tenant')
valid_tenants = []
for tenant in list(tenants):
    valid_tenants.append(tenant['tenant'])

tenant = args.tenant
if tenant not in valid_tenants:
    logger.error(f'{tenant} not a valid tenant, expecting one of: {valid_tenants}')
    sys.exit()

tenant_config = Tenant.objects.get(pk=tenant)
proper_name = tenant_config.proper_name
temp_directories = tenant_config.tenantdirectory_set.all().values('directory')
tenant_directories = []
for dir in list(temp_directories):
    tenant_directories.append(dir['directory'])
temp_recipients = tenant_config.tenantrecipient_set.all().values('recipient')
tenant_recipients = []
for rec in list(temp_recipients):
    tenant_recipients.append(rec['recipient'])

def send_email(plot_path, week_begin, week_end, jupyterhub_stats):
    sender_email = "no-reply@tacc.cloud"
    receiver_emails = tenant_recipients
    primary_receiver = tenant_config.primary_receiver

    message = MIMEMultipart()
    message['Subject'] = f"{proper_name} JupyterHub Usage for {week_begin} - {week_end}"
    message['From'] = sender_email
    message['To'] = primary_receiver
    message.preamble = f"{proper_name} JupyterHub Usage for {week_begin} - {week_end}"

    with open(plot_path, 'rb') as fp:
        img = MIMEImage(fp.read())
        img.add_header('Content-Disposition', 'attachment', filename='dir_usage.png')
        img.add_header('X-Attachment-Id', '0')
        img.add_header('Content-ID', '<0>')
        fp.close()
        message.attach(img)

    html = """\
    <html>
        <body>
            <h1 style="text-align: center;">
                """+str(proper_name)+""" JupyterHub Directory Usage
            </h1>
            <h4>
                Unique Users (distinct user count): """+str(jupyterhub_stats['unique_user_count'])+"""
            </h4>
            <h4>
                Total Logins (total login count): """+str(jupyterhub_stats['total_login_count'])+"""
            </h4>
            <h4>
                Unique Logins (distinct login count): """+str(jupyterhub_stats['unique_login_count'])+"""
            </h4>
            <h4>
                Number of Notebooks Opened: """+str(jupyterhub_stats['num_opened_files'])+"""
            </h4p>
            <h4>
                Number of Notebooks Created: """+str(jupyterhub_stats['num_created_files'])+"""
            </h4>
            <p><img src="cid:0"></p>
        </body>
    </html>
    """
    message.attach(MIMEText(html, 'html'))

    try:
        server = smtplib.SMTP(host, port)
        server.sendmail(sender_email, receiver_emails, message.as_string())
        logger.debug("EMAIL SENT")
        if os.path.isfile(plot_path):
            os.remove(plot_path)
    except Exception as e:
        logger.debug(f'ERROR SENDING EMAIL: {e}')

def create_graph(directories, counts):
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

def get_directories_and_counts(accessed_files):
    filepaths = list(accessed_files)
    dir_counts = {}
    directories = tenant_directories

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

def generate_stats(accessed_files, week_begin, week_end):
    created_files = accessed_files.filter(action='created')
    opened_files = accessed_files.filter(action='opened')

    num_created_files = created_files.count()
    num_opened_files = opened_files.count()

    login_users = LoginLog.objects.filter(tenant=tenant, date__range=(week_begin, week_end))
    unique_login_count = login_users.values('user').distinct().count()
    total_login_count = login_users.count()

    try:
        combined = list(chain(accessed_files, login_users))
        users = []
        for log in combined:
            users.append(log.user)
        unique_users = set(users)
        unique_user_count = len(unique_users)
    except Exception as e:
        unique_user_count = 'Error getting unique user count'

    jupyterhub_stats = {
        'num_created_files': num_created_files,
        'num_opened_files': num_opened_files,
        'unique_login_count': unique_login_count,
        'total_login_count': total_login_count,
        'unique_user_count': unique_user_count
    }
    return jupyterhub_stats

if __name__ == '__main__':
    week_end = date.date.today() - date.timedelta(days=1)
    week_begin = week_end - date.timedelta(days=6)

    accessed_files = FileLog.objects.filter(tenant=tenant, date__range=(week_begin, week_end))
    directories, counts = get_directories_and_counts(accessed_files.values('filepath'))
    plot_path = create_graph(directories, counts)
    jupyterhub_stats = generate_stats(accessed_files, week_begin, week_end)

    send_email(plot_path, week_begin, week_end, jupyterhub_stats)