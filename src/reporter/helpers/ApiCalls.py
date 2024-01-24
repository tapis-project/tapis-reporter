import os
import django
import logging
from django.conf import settings
import requests

from serpapi import GoogleSearch

from ..apps.services.tapis.models import Paper


logger = logging.getLogger(__name__)

os.environ["DJANGO_SETTINGS_MODULE"] = "reporter.settings"
django.setup()


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
    papers_url = requests.get('https://raw.githubusercontent.com/tapis-project/tapis-reporting/main/tapis_papers.json')
    papers_data = papers_url.json()

    logger.error(f'papers_data: {papers_data}')

    tapis_papers = []

    for paper_source in papers_data:
        if paper_source['source'] == 'googlescholar':
            papers = []
            author_id = paper_source['available_with_id']

            for paper in paper_source['papers']:
                papers.append(paper['title'])

            for i in range(paper_source['pages_needed']):
                offset = i * 20

                params = {
                    "engine": "google_scholar_author",
                    "hl": "en",
                    "author_id": author_id,
                    "start": offset,
                    "api_key": settings.SERP_API_KEY
                }

                search = GoogleSearch(params)
                results = search.get_dict()
                articles = results['articles']

                for article in articles:
                    if article['title'] in papers:
                        authors = article['authors'].split(',')
                        co_authors = ','.join(authors[1:])

                        paper = Paper(
                            title=article['title'],
                            primary_author=authors[0],
                            publication_source=article['publication'],
                            publication_date=article['year'],
                            co_authors=co_authors,
                            citation_url=article['link'],
                            citations=article['cited_by']['value']
                        )

                        tapis_papers.append(paper)

        if paper_source['source'] == 'researchgate':
            for article in paper_source['papers']:
                paper = Paper(
                    title=article['title'],
                    primary_author=article['primary_author'],
                    publication_source=article['publication_source'],
                    publication_date=article['publication_date'],
                    co_authors=','.join(article['co_authors']),
                    citation_url=article['citation_url'],
                    citations=article['citations']
                )
                tapis_papers.append(paper)

    logger.error(f'tapis_papers in get_tapis_papers function: {tapis_papers}')

    status = save_tapis_papers(tapis_papers)
    return status


if __name__ == '__main__':
    get_tapis_papers()