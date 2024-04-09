import os
import django
import logging
from django.conf import settings
import requests

from serpapi import GoogleSearch

logger = logging.getLogger(__name__)

os.environ["DJANGO_SETTINGS_MODULE"] = "reporter.settings"
django.setup()

from ..apps.tapis.models import Paper


def save_tapis_papers(tapis_papers):
    """
    Add tapis papers to database

    :return: Bool -- True or False
    """
    try:
        Paper.objects.bulk_create(tapis_papers)
        return True
    except Exception as e:
        logger.error(f"Unable to add tapis papers; error: {e}")
        return False


def get_tapis_papers():
    papers_url = requests.get(
        "https://raw.githubusercontent.com/tapis-project/tapis-reporting/main/tapis_papers.json"
    )
    papers_data = papers_url.json()

    logger.debug(f"papers_data: {papers_data}")

    status = save_tapis_papers(papers_data)
    return status
