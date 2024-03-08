from django.shortcuts import render, redirect
from django.template import loader
from django.db.models import Q
from django.conf import settings
from django.contrib.auth.decorators import login_required
import ast
import logging
import random
import requests
from .models import Paper, TenantServiceUsage, JobsData, TapisInfo

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
            tenants = []
            for gateway in gateways_data:
                tenants.append(gateway["tenant"])

            tenants = set(tenants)
            context["tenants"] = tenants

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

    elif request.method == "POST":
        logger.debug(f"In {request.method} method of add_paper")

        context = {"error": False}

        paper_data = build_paper_data(request.POST)
        create_paper(paper_data)

        return redirect("tapis:paper")


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
def jobs(request):
    if request.method == "GET":
        logger.debug(f"In {request.method} method of jobs")
        template = loader.get_template("tapis/jobs.html")

        context = {
            "error": False,
        }

        try:
            # load gateways file data
            jobs_data = get_jobs_data()
            context["jobs_data"] = jobs_data
        except Exception as e:
            logger.error(f"Error fetching jobs data: {e}")
        
        return HttpResponse(template.render(context, request))


@login_required
def tapis(request):
    if request.method == "GET":
        logger.debug(f"In {request.method} method of tapis")
        template = loader.get_template("tapis/tapis.html")

        context = {"error": False}

        try:
            # load gateways file data
            tapis_data = get_tapis_data()

            context["tenants"] = tapis_data["tenants"]
            context["num_tokens"] = tapis_data["num_tokens"]
            context["num_unique_users"] = tapis_data["num_unique_users"]
            context["num_ctr_apps"] = tapis_data["num_ctr_apps"]
        except Exception as e:
            logger.error(f"Error fetching tapis data: {e}")

        return HttpResponse(template.render(context, request))

    elif request.method == "POST":
        logger.debug(f"In {request.method} method of tapis")
        template = loader.get_template("tapis/tapis.html")

        context = {"error": False}

        tenant = request.POST.get("tenant")
        try:
            tenant_data = get_tenant_data(tenant)

            context["tenant_queried"] = True
            context["tenant"] = tenant
            context["num_tokens"] = tenant_data.num_tokens
            context["num_unique_users"] = tenant_data.num_unique_users
            context["num_ctr_apps"] = tenant_data.num_ctr_apps
        except Exception as e:
            logger.error(f"Error fetching tenant data: {e}")

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
        if "raw_tapis" in request.POST:
            template = loader.get_template("tapis/raw_splunk_data.html")

        context = {"error": False}

        logger.debug(request.POST)

        tenant = request.POST.get("tenant")
        service = request.POST.get("service")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")

        logger.debug(start_time, end_time)

        tapis_data = load_tapis_data(tenant, service, start_date, end_date, start_time, end_time)
        context["tapis_data"] = tapis_data

        service_counts = {}
        labels = []
        data = []

        for td in tapis_data:
            service_counts[td['service']] = service_counts.get(td['service'], 0) + td['count']

        for key, value in service_counts.items():
            labels.append(key)
            data.append(value)

        labels.append(td['service'])
        data.append(td['count'])

        background_colors = get_background_colors(data)

        context["tenant"] = tenant.upper()
        context["labels"] = labels
        context["data"] = data
        context["backgroundColors"] = background_colors

        return HttpResponse(template.render(context, request))


def get_background_colors(data):
    color = ["#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)]) for i in range(len(data))]
    return color


def build_paper_data(data):
    return {
        "title": data.get("title"),
        "primary_author": data.get("author"),
        "publication_source": data.get("source"),
        "publication_date": data.get("date"),
        "co_authors": data.get("coauthors"),
        "citation_url": data.get("citation"),
    }


def create_paper(paper_data):
    paper = Paper(
        title=paper_data["title"],
        primary_author=paper_data["primary_author"],
        publication_source=paper_data["publication_source"],
        publication_date=paper_data["publication_date"],
        co_authors=paper_data["co_authors"],
        citation_url=paper_data["citation_url"],
        citations=0
    )
    Paper.objects.create(paper)


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


def get_tapis_data():
    logger.debug("Attempting to fetch tapis data")
    tapis_data = TapisInfo.objects.all()

    tapis_stats = {}
    for tenant in tapis_data:
        if "tenants" in tapis_stats:
            tapis_stats["tenants"].append(tenant.tenant)
        else:
            tapis_stats["tenants"] = [tenant.tenant]
        tapis_stats["num_tokens"] = tapis_stats.get("num_tokens", 0) + tenant.num_tokens
        tapis_stats["num_unique_users"] = tapis_stats.get("num_unique_users", 0) + tenant.num_unique_users
        tapis_stats["num_ctr_apps"] = tapis_stats.get("num_ctr_apps", 0) + tenant.num_ctr_apps

    return tapis_stats


def get_tenant_data(tenant):
    logger.debug("Attempting to fetch tapis data")
    tenant_data = TapisInfo.objects.get(tenant=tenant)
    logger.debug(f"Tenant data retrieved: {tenant_data}")

    return tenant_data


def get_jobs_data():
    logger.debug("Attempting to fetch jobs data")
    jobs_data = JobsData.objects.get(id=1)
    dev_daily_tup = ast.literal_eval(jobs_data.dev_daily_jobs)
    jobs_data.dev_daily_jobs = float(dev_daily_tup[0])
    logger.debug(f"Job data retrieved: {jobs_data}")

    return jobs_data


def load_tapis_data(tenant, service, start_date, end_date, start_time, end_time):
    logger.info("in load tapis data for html")
    query = Q()

    if tenant and tenant != "null" and tenant != "":
        query &= Q(tenant=tenant)
    else:
        return None

    if service and service != "null" and service != "":
        query &= Q(service=service)

    if start_time and start_time != "null" and start_time != "":
        query &= Q(start_time__gte=start_time)

    if end_time and end_time != "null" and end_time != "":
        query &= Q(end_time__lte=end_time)

    query &= Q(log_date__gte=start_date)
    query &= Q(log_date__lte=end_date)

    tenant_service_qs = TenantServiceUsage.objects.filter(query)

    tapis_data = []

    for tenant_service_data in tenant_service_qs:
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

    return tapis_data


def load_tapis_papers():
    logger.error("in get tapis papers for html")
    tapis_papers_qs = Paper.objects.all()
    logger.error("Tapis papers queryset retrieved")
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
