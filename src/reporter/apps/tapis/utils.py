import ast
import json
import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import django
import github
from django.conf import settings

logger = logging.getLogger(__name__)

os.environ["DJANGO_SETTINGS_MODULE"] = "reporter.settings"
django.setup()


def build_tapis_email(data) -> MIMEMultipart:
    sender_email = "no-reply@tacc.cloud"
    primary_receiver = data["primary_receiver"]
    week_begin = data["week_begin"]
    week_end = data["week_end"]

    message = MIMEMultipart()
    message["Subject"] = f"Jobs Data for {week_begin} - {week_end}"

    message["From"] = sender_email
    message["To"] = primary_receiver

    message.preamble = f"Jobs Data for {week_begin} - {week_end}"

    v2_data = data["v2"]
    v2_data = dict(
        sorted(v2_data.items(), key=lambda v2_data: int(v2_data[1]), reverse=True)
    )
    v2_total = 0
    v2_table_data = []
    for tenant in v2_data:
        v2_table_data.append(
            f"""<tr><td style="border: 1px solid #000000; text-align: left; padding: 8px;"> {tenant} </td><td style="border: 1px solid #000000; text-align: left; padding: 8px;"> {v2_data[tenant]} </td></tr>"""
        )
        v2_total += int(v2_data[tenant])
    v2_table_rows = "\n".join(v2_table_data)

    v3_data = data["v3"]
    v3_data = dict(
        sorted(v3_data.items(), key=lambda v3_data: int(v3_data[1]), reverse=True)
    )
    v3_total = 0
    v3_table_data = []
    for tenant in v3_data:
        v3_table_data.append(
            f"""<tr><td style="border: 1px solid #000000; text-align: left; padding: 8px;"> {tenant} </td><td style="border: 1px solid #000000; text-align: left; padding: 8px;"> {v3_data[tenant]} </td></tr>"""
        )
        v3_total += int(v3_data[tenant])
    v3_table_rows = "\n".join(v3_table_data)

    html = """\
    <html>
        <body>
            <h1 style="text-align: center;">
                Tapis Jobs Data {week_begin} - {week_end}
            </h1>
            <h2>
                v2 Jobs Data: \n
            </h2>
                <table style="font-family: arial, sans-serif; border-collapse: collapse; width: 100%;">
                    <th style="border: 1px solid #000000; text-align: left; padding: 8px;">
                        Tenant
                    </th>
                    <th style="border: 1px solid #000000; text-align: left; padding: 8px;">
                        Count
                    </th>
                    {v2_table_rows}
                </table>
                <h3>
                    Total: {v2_total}
                </h3>
            <h2>
                v3 Jobs Data: \n
            </h2>
                <table style="font-family: arial, sans-serif; border-collapse: collapse; width: 100%;">
                    <th style="border: 1px solid #000000; text-align: left; padding: 8px;">
                        Tenant
                    </th>
                    <th style="border: 1px solid #000000; text-align: left; padding: 8px;">
                        Count
                    </th>
                    {v3_table_rows}
                </table>
                <h3>
                    Total: {v3_total}
                </h3>
        </body>
    </html>
    """

    # v2_table_data.append(['Tenant', 'Count'])
    # for tenant in v2_data:
    #     v2_table_data.append([tenant, v2_data[tenant]])

    # v3_data = data["v3"]
    # v3_table_data = []
    # v3_table_data.append(['Tenant', 'Count'])
    # for tenant in v3_data:
    #     v3_table_data.append([tenant, v3_data[tenant]])

    html = html.format(
        week_begin=str(week_begin),
        week_end=str(week_end),
        v2_table_rows=v2_table_rows,
        v2_total=v2_total,
        v3_table_rows=v3_table_rows,
        v3_total=v3_total,
    )
    message.attach(MIMEText(html, "html"))

    return message


def upload_to_github(data_obj, filename, message, branch):
    try:
        g = github.Github(settings.TAPIS_GITHUB_TOKEN)
        repo = g.get_repo("tapis-project/tapis-reporting")
        contents = repo.get_contents(filename)
        content_str = (contents.decoded_content).decode("utf-8")

        content_obj = ast.literal_eval(content_str)

        content_obj.append(data_obj)

        logger.debug(f"Attempting to update {filename} with {data_obj}")
        repo.update_file(
            contents.path,
            message,
            json.dumps(content_obj, indent=4),
            contents.sha,
            branch=branch,
        )

        logger.debug(f"Successfully updated {filename}")
    except Exception as e:
        logger.error(f"Unable to update {filename}: {e}")
        return False

    return True
