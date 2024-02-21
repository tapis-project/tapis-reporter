from django.shortcuts import render, redirect
from django.template import loader
from django.db.models import Q
from django.conf import settings
from django.contrib.auth.decorators import login_required
import logging
import requests
from .models import Paper, TenantServiceUsage

logger = logging.getLogger(__name__)

# Create your views here.
from django.http import HttpResponse


@login_required
def index(request):
    if request.method == "GET":
        template = loader.get_template("tapis/index.html")

        context = {
            "error": False,
            "tapisdocs": "https://tapis.readthedocs.io/en/latest/technical/index.html",
        }

        return HttpResponse(template.render(context, request))


@login_required
def tenants(request):
    if request.method == "GET":
        template = loader.get_template("tapis/tenants.html")

        context = {
            "error": False,
        }

        try:
            tenants_call = requests.get("https://tacc.tapis.io/v3/tenants")
            tenants_info = tenants_call.json()["result"]

            tenants = []
            for tenant_info in tenants_info:
                owner = tenant_info["owner"]
                owner_call = requests.get(
                    f"https://tacc.tapis.io/v3/tenants/owners/{owner}"
                )
                owner_info = owner_call.json()["result"]

                tenant = build_tenant_model(tenant_info, owner_info)

                tenants.append(tenant)
        except Exception as e:
            context["error"] = True
            context["message"] = e
        else:
            context["tenants"] = tenants
            context["tenant_count"] = len(tenants)

        return HttpResponse(template.render(context, request))


@login_required
def trainings(request):
    if request.method == "GET":
        logger.debug(f"In {request.method} method of trainings")
        template = loader.get_template("tapis/training.html")

        context = {
            "error": False,
        }

        try:
            trainings_url = requests.get(
                "https://raw.githubusercontent.com/tapis-project/tapis-reporting/main/tapis_training.json"
            )

            trainings_data = trainings_url.json()
            context["trainings_data"] = trainings_data
        except Exception as e:
            logger.error(f"ERROR: {e}")
            context["error"] = True
            context["message"] = e

        return HttpResponse(template.render(context, request))


@login_required
def gateways(request):
    if request.method == "GET":
        logger.debug(f"In {request.method} method of gateways")
        template = loader.get_template("tapis/gateways.html")

        context = {
            "error": False,
        }

        try:
            # load gateways file data
            gateways_data = get_gateways_data()

            # get number of gateways
            num_gateways = len(gateways_data)

            # misc data
            oldest_gateway = get_oldest_gateway(gateways_data)

            context["gateways_data"] = gateways_data
            context["num_gateways"] = num_gateways
            context["oldest_gateway"] = oldest_gateway["release_year"]

        except Exception as e:
            logger.error(f"ERROR: {e}")
            context["error"] = True
            context["message"] = e

        return HttpResponse(template.render(context, request))

    elif request.method == "POST":
        logger.debug(f"In {request.method} method of gateways")
        template = loader.get_template("tapis/gateways.html")

        context = {
            "error": False,
        }

        tenant = request.POST.get("tenant")
        if "tenants_gateways" in request.POST:
            return redirect("tapis:tenant_gateways", tenant=tenant)


@login_required
def tenant_gateways(request, tenant):
    if request.method == "GET":
        logger.debug(f"In {request.method} method of tenant gateways")
        template = loader.get_template("tapis/tenant_gateways.html")

        context = {"error": False, "tenant": tenant}

        try:
            tenant_gateways = get_gateways_for_tenant(tenant)
            context["tenant_gateways"] = tenant_gateways
            context["gateway_count"] = len(tenant_gateways)

            oldest_gateway = get_oldest_gateway(tenant_gateways)
            latest_gateway = get_latest_gateway(tenant_gateways)
            context["oldest_gateway"] = oldest_gateway["release_year"]
            context["latest_gateway"] = latest_gateway["release_year"]

        except Exception as e:
            logger.error(f"ERROR: {e}")
            context["error"] = True
            context["message"] = e

        return HttpResponse(template.render(context, request))


@login_required
def github(request):
    if request.method == "GET":
        logger.debug(f"In {request.method} method of github")
        template = loader.get_template("tapis/github.html")

        context = {"error": False}

        repos = get_repos("tapis-project")

        context["repos"] = repos

        return HttpResponse(template.render(context, request))


@login_required
def papers(request):
    if request.method == "GET":
        logger.debug(f"In {request.method} method of papers")
        template = loader.get_template("tapis/papers.html")

        context = {"error": False}

        try:
            tapis_papers = load_tapis_papers()
            logger.error(f"tapis papers in papers html: {tapis_papers}")
            context["tapis_papers"] = tapis_papers

        except Exception as e:
            context["error"] = True
            context["message"] = e

        return HttpResponse(template.render(context, request))

    elif request.method == "POST":
        logger.debug(f"In {request.method} method of papers")

        context = {"error": False}

        return redirect("tapis:add_paper")


@login_required
def add_paper(request):
    if request.method == "GET":
        logger.debug(f"In {request.method} method of add_paper")
        template = loader.get_template("tapis/add_paper.html")

        context = {"error": False}

        return HttpResponse(template.render(context, request))


@login_required
def streams(request):
    if request.method == "GET":
        logger.debug(f"In {request.method} method of streams")
        template = loader.get_template("tapis/streams.html")

        context = {"error": False}

        try:
            streams_data = get_streams_data()
            context["streams_data"] = streams_data

        except Exception as e:
            context["error"] = True
            context["message"] = e

        return HttpResponse(template.render(context, request))


@login_required
def splunk(request):
    if request.method == "GET":
        logger.debug(f"In {request.method} method of Splunk")
        template = loader.get_template("tapis/splunk_data_form.html")

        context = {"error": False}

        return HttpResponse(template.render(context, request))

    elif request.method == "POST":
        logger.debug(f"In {request.method} method of Splunk")
        template = loader.get_template("tapis/splunk_data.html")

        context = {"error": False}

        logger.debug(request.POST)

        tenant = request.POST.get("tenant")
        service = request.POST.get("service")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")

        tapis_data = load_tapis_data(tenant, service, start_date, end_date)
        context["tapis_data"] = tapis_data
        return HttpResponse(template.render(context, request))


def build_tenant_model(tenant_info, owner_info):
    tenant = {
        "tenant_id": tenant_info["tenant_id"],
        "site_id": tenant_info["site_id"],
        "description": tenant_info["description"],
        "name": owner_info["name"],
        "email": tenant_info["owner"],
        "institution": owner_info["institution"],
        "date_created": owner_info["create_time"],
        "last_updated": owner_info["last_update_time"],
    }
    return tenant


def get_streams_data():

    # Might have to update to use different tapis tokens dependent on tenant
    tenant = {"key_name": "TAPIS_SERVICE_TOKEN"}
    headers = {
        "x-tapis-token": getattr(
            settings, tenant["key_name"], settings.TAPIS_SERVICE_TOKEN
        )
    }

    streams = requests.get(
        f"https://{tenant}.tapis.io/v3/streams/metrics", headers=headers
    )

    amount_data_streamed = 0
    number_data_streams = len(streams.json())
    number_archives_registered = 0

    streams_data = []

    for stream in streams.json():
        amount_data_streamed = amount_data_streamed + int(stream["size"])
        if stream["type"] == "archive":
            number_archives_registered = number_archives_registered + 1

    stream_data = {
        "tenant": tenant.name,
        "amount_data_streamed": amount_data_streamed,
        "number_data_streams": number_data_streams,
        "number_archives_registered": number_archives_registered,
    }

    streams_data.append(stream_data)

    return streams_data


def load_tapis_data(tenant, service, start_date, end_date):
    logger.info("in load tapis data for html")
    query = Q()

    if tenant and tenant != "null" and tenant != "":
        query &= Q(tenant=tenant)
    else:
        return None

    if service and service != "null" and service != "":
        query &= Q(service=service)

    query &= Q(log_date__gte=start_date)
    query &= Q(log_date__lte=end_date)

    tenant_service_qs = TenantServiceUsage.objects.filter(query)

    logger.info(f"tenant_service_qs: {tenant_service_qs}")
    tapis_data = []

    for tenant_service_data in tenant_service_qs:
        logger.error(f"tapis_data: {tenant_service_data}")
        tapis_data.append(
            {
                "date": tenant_service_data.log_date,
                "start_time": tenant_service_data.start_time,
                "end_time": tenant_service_data.end_time,
                "tenant": tenant_service_data.tenant,
                "service": tenant_service_data.service,
                "count": tenant_service_data.log_count,
            }
        )

    logger.error(f"all data from db: {tapis_data}")

    return tapis_data


def load_tapis_papers():
    logger.error("in get tapis papers for html")
    tapis_papers_qs = Paper.objects.all()
    logger.error(f"tapis_papers_qs: {tapis_papers_qs}")
    tapis_papers = []

    for paper in tapis_papers_qs:
        logger.error(f"paper: {paper}")
        tapis_papers.append(
            {
                "title": paper.title,
                "primary_author": paper.primary_author,
                "publication_source": paper.publication_source,
                "publication_date": paper.publication_date,
                "co_authors": paper.co_authors,
                "citation_url": paper.citation_url,
                "citations": paper.citations,
            }
        )

    logger.error(f"tapis_papers from db: {tapis_papers}")

    return tapis_papers


def get_gateways_data():
    gateways_url = requests.get(
        "https://raw.githubusercontent.com/tapis-project/tapis-reporting/main/tapis_gateways.json"
    )
    gateways_data = gateways_url.json()

    gateways_data = populate_missing_gateway_data(gateways_data)

    return gateways_data


def get_gateways_for_tenant(tenant):
    gateways_data = get_gateways_data()

    tenant_gateways = []
    for gateway in gateways_data:
        logger.error(f"gateway: {gateway}")
        if gateway["tenant"] == tenant:
            gateway_info = {
                "name": gateway["name"],
                "urls": gateway["urls"],
                "release_year": gateway["release_year"],
            }
            tenant_gateways.append(gateway_info)

    return tenant_gateways


def populate_missing_gateway_data(gateways_data):
    temp_gateways_data = gateways_data
    for gateway in temp_gateways_data:
        logger.error(f"gateway: {gateway}")

        if gateway["tenant"] == "":
            gateway["tenant"] = "N/A"

        if gateway["release_year"] == "":
            gateway["release_year"] = "N/A"

        if len(gateway["urls"]) > 1:
            urls = ""
            for url in gateway["urls"]:
                urls = urls + url + ", "
        else:
            urls = gateway["urls"][0]

        gateway["urls"] = urls

    return temp_gateways_data


def get_oldest_gateway(gateways):
    return min(gateways, key=lambda x: x["release_year"])


def get_latest_gateway(gateways):
    return max(gateways, key=lambda x: x["release_year"])


def get_repos(org):
    repos_with_counts = []
    try:
        repos = requests.get(f"https://api.github.com/orgs/{org}/repos")
        for repo in repos.json():
            if repo["has_issues"]:
                url = "https://api.github.com/graphql"
                headers = {"Authorization": f"bearer {settings.GITHUB_API_TOKEN}"}

                repo_owner = repo["owner"]["login"]
                repo_name = repo["name"]

                query = """
                    query GetRepos($owner: String!, $name: String!) { 
                        repository(owner: $owner, name: $name) { 
                            issues {
                            totalCount
                            }
                        }
                    }
                """
                variables = {"owner": repo_owner, "name": repo_name}

                body = {"query": query, "variables": variables}

                response = requests.post(url=url, headers=headers, json=body)
                total_issues = response.json()["data"]["repository"]["issues"][
                    "totalCount"
                ]

                date = repo["created_at"]

                repo = {
                    "owner": repo_owner,
                    "name": repo_name,
                    "year": date,
                    "total_issues": total_issues,
                }

                repos_with_counts.append(repo)
    except Exception as e:
        logger.error(f"Unable to get repos for: {org}; error: {e}")

    return repos_with_counts
