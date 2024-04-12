import logging
import os

import django
import requests

logger = logging.getLogger(__name__)

os.environ["DJANGO_SETTINGS_MODULE"] = "reporter.settings"
django.setup()

from reporter.apps.tapis.models import Paper, Training


class Populate:
    def __init__(self):
        self.github_url = (
            "https://raw.githubusercontent.com/tapis-project/tapis-reporting/main"
        )

    def populate_trainings(self):
        trainings_url = requests.get(f"{self.github_url}/tapis_trainings.json")

        trainings_data = trainings_url.json()

        logger.debug(trainings_data)

        training_objs = [Training(**training_obj) for training_obj in trainings_data]

        for training_obj in training_objs:
            if training_obj.date == "":
                training_obj.date = "2024-01-01"

        Training.objects.bulk_create(training_objs)

    def populate_papers(self):
        papers_url = requests.get(f"{self.github_url}/tapis_papers.json")
        papers_data = papers_url.json()

        logger.debug(papers_data)

        paper_objects = [Paper(**paper_obj) for paper_obj in papers_data]

        Paper.objects.bulk_create(paper_objects)

    # def populate_gateways(self):
    #     papers_url = requests.get(
    #         f"{self.github_url}/tapis_gateways.json"
    #     )
    #     gateways_data = papers_url.json()

    #     logger.debug(gateways_data)

    #     gateway_objects = [Gateway(**gateway_obj)
    #                      for gateway_obj in gateways_data]

    #     Paper.objects.bulk_create(gateway_objects)


if __name__ == "main":
    populate = Populate()
    populate.populate_trainings()
    populate.populate_papers()
    # populate.populate_gateways()
