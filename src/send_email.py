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

from reporter.helpers import generate_email_data

logger = logging.getLogger(__name__)

os.environ["DJANGO_SETTINGS_MODULE"] = "reporter.settings"
django.setup()


host = 'relay.tacc.utexas.edu'
port = 25

parser = argparse.ArgumentParser(description='Process arguments for email')
parser.add_argument('service')
parser.add_argument('tenant')
args = parser.parse_args()

services = Service.objects.all().values('service')
valid_services = []
for service in list(services):
    valid_services.append(service['service'])

service = args.service
if service not in valid_services:
    logger.error(f'{service} not a valid service, expecting one of: {valid_services}')
    sys.exit()

if services[service]['tenants']


def send_email(plot_path, week_begin, week_end, jupyterhub_stats):
    sender_email = "no-reply@tacc.cloud"
    receiver_emails = service_recipients
    primary_receiver = service_config.primary_receiver

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

def generate_stats(accessed_files, week_begin, week_end):
    created_files = accessed_files.filter(action='created')
    opened_files = accessed_files.filter(action='opened')

    num_created_files = created_files.count()
    num_opened_files = opened_files.count()

    login_users = LoginLog.objects.filter(service=service, date__range=(week_begin, week_end))
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

    data = initialize_data(service, week_begin, week_end)
    accessed_files = FileLog.objects.filter(service=service, date__range=(week_begin, week_end))
    directories, counts = get_directories_and_counts(accessed_files.values('filepath'))
    plot_path = create_graph(directories, counts)
    jupyterhub_stats = generate_stats(accessed_files, week_begin, week_end)

    send_email(plot_path, week_begin, week_end, jupyterhub_stats)