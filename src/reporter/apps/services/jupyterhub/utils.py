import os

import django
import smtplib
import logging

from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


logger = logging.getLogger(__name__)

os.environ["DJANGO_SETTINGS_MODULE"] = "reporter.settings"
django.setup()

host = "relay.tacc.utexas.edu"
port = 25


def send_jupyterhub_email(data, week_begin, week_end):
    sender_email = "no-reply@tacc.cloud"
    receiver_emails = data["tenant_recipients"]
    primary_receiver = data["primary_receiver"]

    message = MIMEMultipart()
    message[
        "Subject"
    ] = f"{data['proper_name']} JupyterHub Usage for {week_begin} - {week_end}"
    message["From"] = sender_email
    message["To"] = primary_receiver
    message.preamble = (
        f"{data['proper_name']} JupyterHub Usage for {week_begin} - {week_end}"
    )

    if not os.path.isfile(data["plot_path"]):
        logger.error("Error Sending Email: Could not find plot")
        return

    with open(data["plot_path"], "rb") as fp:
        img = MIMEImage(fp.read())
        img.add_header("Content-Disposition", "attachment", filename="dir_usage.png")
        img.add_header("X-Attachment-Id", "0")
        img.add_header("Content-ID", "<0>")
        fp.close()
        message.attach(img)

    html = (
        """\
    <html>
        <body>
            <h1 style="text-align: center;">
                """
        + str(data["proper_name"])
        + """ JupyterHub Directory Usage
            </h1>
            <h4>
                Unique Users (distinct user count): """
        + str(data["jupyterhub_stats"]["unique_user_count"])
        + """
            </h4>
            <h4>
                Total Logins (total login count): """
        + str(data["jupyterhub_stats"]["total_login_count"])
        + """
            </h4>
            <h4>
                Unique Logins (distinct login count): """
        + str(data["jupyterhub_stats"]["unique_login_count"])
        + """
            </h4>
            <h4>
                Number of Notebooks Opened: """
        + str(data["jupyterhub_stats"]["num_opened_files"])
        + """
            </h4p>
            <h4>
                Number of Notebooks Created: """
        + str(data["jupyterhub_stats"]["num_created_files"])
        + """
            </h4>
            <p><img src="cid:0"></p>
            <h5>
                Servers with no activity for 7+ Days: """
        + str(data["old_servers"])
        + """
            </h5>
        </body>
    </html>
    """
    )
    message.attach(MIMEText(html, "html"))

    try:
        server = smtplib.SMTP(host, port)
        server.sendmail(sender_email, receiver_emails, message.as_string())
        logger.info("Email sent successfully")
        if os.path.isfile(data["plot_path"]):
            os.remove(data["plot_path"])
    except Exception as e:
        logger.debug(f"Error Sending Email: {e}")
