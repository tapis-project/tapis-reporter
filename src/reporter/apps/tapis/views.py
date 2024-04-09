from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template import loader
from django.db.models import Q
from django.conf import settings
from django.contrib.auth.decorators import login_required
import ast
import logging
import random
import requests
from pandas import date_range
import datetime
from .models import Paper, TenantServiceUsage, JobsData, TapisInfo, Training, TenantJobsData
from .utils import upload_to_github

logger = logging.getLogger(__name__)

# Create your views here.


@login_required
def index(request):
    if request.method == "GET":
        template = loader.get_template("tapis/index.html")

        context = {
            "error": False,
            "tapisdocs": "https://tapis.readthedocs.io/en/latest/technical/index.html",
        }

        try:
            overview_data = generate_overview_data(tenant='tapis')
            context['auth_data'] = overview_data['auth_data']
            context['jobs_data'] = overview_data['jobs_data']
            context['streams_data'] = overview_data['streams_data']
            context['misc_data'] = overview_data['misc_data']

            context['tenants'] = JobsData.objects.values_list('tenant', flat=True)
        except Exception as e:
            logger.error(f"Error generating overview data: {e}")

        return HttpResponse(template.render(context, request))

    elif request.method == "POST":
        template = loader.get_template("tapis/index.html")

        context = {
            "error": False,
            "tapisdocs": "https://tapis.readthedocs.io/en/latest/technical/index.html",
        }

        if "get_issues" in request.POST:
            logger.debug("Getting issues call")
            overview_data = generate_overview_data(tenant='tapis', get_issues=True)
            context['auth_data'] = overview_data['auth_data']
            context["jobs_data"] = overview_data['jobs_data']
            context['streams_data'] = overview_data['streams_data']
            context['misc_data'] = overview_data['misc_data']
            context['tenants'] = JobsData.objects.values_list('tenant', flat=True)
        else:
            try:
                tenant = request.POST.get("tenant")
                start_date = request.POST.get("start_date")
                end_date = request.POST.get("end_date")

                overview_data = generate_overview_data(tenant=tenant)
                context['auth_data'] = overview_data['auth_data']
                context['jobs_data'] = overview_data['jobs_data']
                context['tenants'] = JobsData.objects.values_list('tenant', flat=True)
            except Exception as e:
                logger.error(e)

        return HttpResponse(template.render(context, request))


@login_required
def tenants(request):
    if request.method == "GET":
        template = loader.get_template("tapis/tenants.html")

        context = {
            "error": False,
        }

        tenants = get_tenants()

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
            tapis_traings = load_tapis_trainings()
            context["trainings_data"] = tapis_traings
        except Exception as e:
            logger.error(f"ERROR: {e}")
            context["error"] = True
            context["message"] = e

        return HttpResponse(template.render(context, request))

    if request.method == "POST":
        logger.debug(f"In {request.method} method of trainings")

        logger.debug(f"Got training info: {request.POST}")

        context = {"error": False}

        training_data = build_training_data(request.POST)
        Training.objects.create(**training_data)

        upload_to_github(training_data, "tapis_trainings.json",
                         f"Updating trainings from Tapis Reporter with: {request.POST.get('name')}", "main")

        return redirect("tapis:trainings")


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
            context["new_paper"] = False

        except Exception as e:
            context["error"] = True
            context["message"] = e

        return HttpResponse(template.render(context, request))

    elif request.method == "POST":
        logger.debug(f"In {request.method} method of papers")
        template = loader.get_template("tapis/papers.html")

        logger.debug(f"Got paper info: {request.POST}")

        context = {"error": False}

        paper_data = build_paper_data(request.POST)
        Paper.objects.create(**paper_data)

        upload_to_github(paper_data, "tapis_papers.json",
                         f"Updating papers from Tapis Reporter with: {request.POST.get('title')}", "main")
        return redirect("tapis:papers")


# @login_required
# def add_paper(request):
#     if request.method == "GET":
#         logger.debug(f"In {request.method} method of add_paper")
#         template = loader.get_template("tapis/add_paper.html")

#         context = {"error": False}

#         return HttpResponse(template.render(context, request))

#     elif request.method == "POST":
#         logger.debug(f"In {request.method} method of add_paper")

#         context = {"error": False}

#         paper_data = build_paper_data(request.POST)
#         create_paper(paper_data)

#         return redirect("tapis:paper")


@login_required
def streams(request):
    if request.method == "GET":
        logger.debug(f"In {request.method} method of streams")
        template = loader.get_template("tapis/streams.html")

        context = {"error": False}

        try:
            streams_data = get_streams_data('tacc')
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

        return HttpResponse(template.render(context, request))

    elif request.method == "POST":
        '''
        need list of tenant names for v2 and v3
        generate data array for echart
        need array for v2, and one for v3
        Sample data dictionary
        {
            name: 'icicle',
            emphasis: {
                focus: 'series'
            },
            smooth: true,
            data: [101, 205, 91, 175, 50, 178, 240],
            type: 'line'
        }
        '''
        logger.debug(f"In {request.method} method of jobs")
        template = loader.get_template("tapis/jobs.html")

        context = {
            "error": False,
            "charts": False
        }

        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        query = Q()

        query &= Q(date__gte=start_date)
        query &= Q(date__lte=end_date)

        # tenant, date, count, version
        tenant_jobs_data = TenantJobsData.objects.filter(query)

        v3_jobs_data = tenant_jobs_data.filter(version='v3')
        v2_jobs_data = tenant_jobs_data.filter(version='v2')

        """
        Given objects (tenant, count, date, version)
        for each date, grab tenant and count
        """

        """
        Grab unique tenants for each version
        """
        v3_tenants = list(v3_jobs_data.values_list('tenant', flat=True).distinct())
        v2_tenants = list(v2_jobs_data.values_list('tenant', flat=True).distinct())

        context['v3_tenants'] = v3_tenants
        context['v2_tenants'] = v2_tenants

        """
        Grab dates with jobs for each version
        """
        v3_dates = list(v3_jobs_data.values_list('date', flat=True))
        v2_dates = list(v2_jobs_data.values_list('date', flat=True))

        """
        Convert the datetime objects to strings
        """
        v3_dates = [date.strftime('%Y-%m-%d') for date in v3_dates]
        v2_dates = [date.strftime('%Y-%m-%d') for date in v2_dates]

        chart_dates = sorted({str(d)[:10] for d in date_range(start_date, end_date, freq='d')})

        try:
            v3_start_date = min(v3_dates)
            v3_end_date = max(v3_dates)

            context['v3_start_date'] = v3_start_date
            context['v3_end_date'] = v3_end_date

            try:
                v3_tenants_date_counts = {}
                for v3_tenant in v3_tenants:
                    v3_tenant_date_counts = list(v3_jobs_data.filter(tenant=v3_tenant).values_list('date', 'count'))
                    v3_tenant_date_counts = [(date_count[0].strftime('%Y-%m-%d'), date_count[1]) for date_count in v3_tenant_date_counts]
                    v3_tenants_date_counts[v3_tenant] = v3_tenant_date_counts

                for v3_tenant in v3_tenants:
                    tenant_date_counts = v3_tenants_date_counts[v3_tenant]
                    dates_with_jobs = {d for d,_ in tenant_date_counts}
                    dates_in_range = {str(d)[:10] for d in date_range(start_date, end_date, freq='d')}
                    dates_without_jobs = dates_in_range.difference(dates_with_jobs)

                    v3_tenants_date_counts[v3_tenant] = sorted(tenant_date_counts + [(d, 0) for d in dates_without_jobs])
            except Exception as e:
                logger.debug(f"Error getting v3 tenants_date_counts: {e}")

            v2_start_date = min(v2_dates)
            v2_end_date = max(v2_dates)

            context['v2_start_date'] = v2_start_date
            context['v2_end_date'] = v2_end_date

            try:
                v2_tenants_date_counts = {}
                for v2_tenant in v2_tenants:
                    v2_tenant_date_counts = list(v2_jobs_data.filter(tenant=v2_tenant).values_list('date', 'count'))
                    v2_tenant_date_counts = [(date_count[0].strftime('%Y-%m-%d'), date_count[1]) for date_count in v2_tenant_date_counts]
                    v2_tenants_date_counts[v2_tenant] = v2_tenant_date_counts

                for v2_tenant in v2_tenants:
                    tenant_date_counts = v2_tenants_date_counts[v2_tenant]
                    dates_with_jobs = {d for d,_ in tenant_date_counts}
                    dates_in_range = {str(d)[:10] for d in date_range(start_date, end_date, freq='d')}
                    dates_without_jobs = dates_in_range.difference(dates_with_jobs)

                    v2_tenants_date_counts[v2_tenant] = sorted(tenant_date_counts + [(d, 0) for d in dates_without_jobs])
            except Exception as e:
                logger.debug(f"Error getting v2 tenants_date_counts: {e}")

        except Exception as e:
            logger.debug(e)

        context['chart_dates'] = chart_dates

        """
        Build series objects for each tenant per day
        """
        v3_series = []
        v2_series = []

        for v3_tenant in v3_tenants:
            v3_tenant_counts = [count for _, count in v3_tenants_date_counts[v3_tenant]]
            v3_series.append(
                {
                    "name": v3_tenant,
                    "emphasis": {
                        "focus": 'series'
                    },
                    "smooth": "true",
                    "data": v3_tenant_counts,
                    "type": 'line',
                }
            )

        for v2_tenant in v2_tenants:
            v2_tenant_counts = [count for _, count in v2_tenants_date_counts[v2_tenant]]
            v2_series.append(
                {
                    "name": v2_tenant,
                    "emphasis": {
                        "focus": 'series'
                    },
                    "smooth": "true",
                    "data": v2_tenant_counts,
                    "type": 'line',
                }
            )

        context['v3_series'] = v3_series
        context['v2_series'] = v2_series

        if v3_series or v2_series:
            context["charts"] = True

        return HttpResponse(template.render(context, request))


@login_required
def tapis(request):
    if request.method == "GET":
        logger.debug(f"In {request.method} method of tapis")
        template = loader.get_template("tapis/tapis.html")

        context = {"error": False}

        try:
            # load gateways file data
            tapis_data = get_tapis_data(tenant)

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
            tenants = request.POST.get("tenants")
            tenants = tenants.replace(" ", "")
            tenants = tenants.replace("[", "")
            tenants = tenants.replace("]", "")
            tenants = tenants.replace("'", "")
            tenants = tenants.split(',')

            context["tenant_queried"] = True
            context["tenant"] = tenant
            context["tenants"] = tenants
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

        logger.debug(start_date)
        logger.debug(end_date)

        # try:
        tapis_data = load_tapis_splunk_data(
            tenant, service, start_date, end_date)

        logger.debug(tapis_data)
        context["tapis_data"] = tapis_data
        context["tenant"] = tenant.upper()
            # if "raw_tapis" in request.POST:
            #     template = loader.get_template("tapis/raw_splunk_data.html")
            #     return HttpResponse(template.render(context, request))
        # except Exception as e:
        #     logger.debug(f"Error getting tapis data: {e}")
        #     return redirect("tapis:splunk")

        service_counts = {}
        labels = []
        data = []

        for td in tapis_data:
            service_counts[td['service']] = service_counts.get(
                td['service'], 0) + td['count']

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
    color = ["#"+''.join([random.choice('0123456789ABCDEF')
                         for j in range(6)]) for i in range(len(data))]
    return color


def build_paper_data(data):
    return {
        "title": data.get("title"),
        "primary_author": data.get("author"),
        "publication_source": data.get("source"),
        "publication_year": data.get("date"),
        "co_authors": data.get("co_authors").split('\r\n'),
        "citation_url": data.get("citation"),
        "citations": data.get("citations")
    }


def build_training_data(data):
    return {
        "name": data.get("name"),
        "forum": data.get("forum"),
        "date": data.get("date"),
        "num_attendees": data.get("num_attendees")
    }


def create_paper(paper_data):
    Paper.objects.create(**paper_data)


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


def get_streams_data(tenant: str = ''):
    # Might have to update to use different tapis tokens dependent on tenant
    logger.debug("get streams data")
    tenant = {"key_name": "TAPIS_SERVICE_TOKEN"}
    headers = {
        "x-tapis-token": settings.TAPIS_SERVICE_TOKEN
    }

    streams = requests.get(
        "https://tacc.tapis.io/v3/streams/metrics", headers=headers
    )

    amount_data_streamed = 0
    number_data_streams = len(streams.json())
    number_archives_registered = 0

    streams_data = []

    for stream in streams.json():
        amount_data_streamed = amount_data_streamed + int(stream["size"])
        if stream["type"] == "archive":
            number_archives_registered = number_archives_registered + 1

    logger.debug(streams_data)
    stream_data = {
        "tenant": "tacc",
        "amount_data_streamed": amount_data_streamed,
        "number_data_streams": number_data_streams,
        "number_archives_registered": number_archives_registered,
    }

    streams_data.append(stream_data)

    return streams_data


def get_tapis_data():
    logger.debug("Attempting to fetch tapis data")
    tapis_info = TapisInfo.objects.all()

    tapis_data = {}
    for tenant in tapis_info:
        if "tenants" in tapis_data:
            tapis_data["tenants"].append(tenant.tenant)
        else:
            tapis_data["tenants"] = [tenant.tenant]
        tapis_data["num_tokens"] = tapis_data.get(
            "num_tokens", 0) + tenant.num_tokens
        tapis_data["num_unique_users"] = tapis_data.get(
            "num_unique_users", 0) + tenant.num_unique_users
        tapis_data["num_ctr_apps"] = tapis_data.get(
            "num_ctr_apps", 0) + tenant.num_ctr_apps

    logger.debug(tapis_data)
    return tapis_data


def get_tenant_data(tenant):
    logger.debug("Attempting to fetch tenant tapis data")
    tenant_data = TapisInfo.objects.get(tenant=tenant)
    logger.debug(f"Tenant data retrieved: {tenant_data}")

    return {
        "num_tokens": tenant_data.num_tokens,
        "num_unique_users": tenant_data.num_unique_users,
        "num_ctr_apps": tenant_data.num_ctr_apps
    }


def get_auth_data(tenant):
    logger.debug(f"Get auth data for {tenant}")
    if tenant != 'tapis':
        return get_tenant_data(tenant)
    else:
        return get_tapis_data()


def get_jobs_data(tenant: str = ''):
    logger.debug(f"Attempting to fetch jobs data for {tenant}")
    jobs_data = JobsData.objects.get(tenant=tenant)
    dev_daily_jobs = ast.literal_eval(jobs_data.dev_daily_jobs)
    jobs_data.dev_daily_jobs = float(dev_daily_jobs)
    logger.debug(f"Job data retrieved: {jobs_data}")

    return jobs_data


def load_tapis_splunk_data(tenant, service, start_date, end_date, start_time = '', end_time = ''):
    logger.info("in load tapis splunk data for html")
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

    logger.debug(tenant_service_qs)

    tapis_data = []

    for tenant_service_data in tenant_service_qs:
        tapis_data.append(
            {
                "date": tenant_service_data.log_date,
                "start_time": tenant_service_data.start_time,
                "end_time": tenant_service_data.end_time,
                "service": tenant_service_data.service,
                "count": tenant_service_data.log_count,
            }
        )

    logger.debug(tapis_data)
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
                "publication_year": paper.publication_year,
                "co_authors": paper.co_authors,
                "citation_url": paper.citation_url,
                "citations": paper.citations,
            }
        )

    logger.error(f"tapis_papers from db: {tapis_papers}")

    return tapis_papers


def load_tapis_trainings():
    logger.debug("in get tapis training for html")
    tapis_trainings_qs = Training.objects.all()
    logger.debug("Tapis papers queryset retrieved")
    tapis_trainings = []

    for training in tapis_trainings_qs:
        logger.debug(f"training: {training}")
        tapis_trainings.append(
            {
                "name": training.name,
                "forum": training.forum,
                "date": training.date,
                "num_attendees": training.num_attendees,
            }
        )

    logger.error(f"tapis_trainings from db: {tapis_trainings}")

    return tapis_trainings


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
                headers = {
                    "Authorization": f"bearer {settings.GITHUB_API_TOKEN}"}

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
        repos_with_counts = sorted(repos_with_counts, key=lambda d: d['total_issues'], reverse=True)
    except Exception as e:
        logger.error(f"Unable to get repos for: {org}; error: {e}")

    return repos_with_counts


def get_tenants():
    tenants = []
    try:
        tenants_call = requests.get("https://tacc.tapis.io/v3/tenants")
        tenants_info = tenants_call.json()["result"]

        for tenant_info in tenants_info:
            owner = tenant_info["owner"]
            owner_call = requests.get(
                f"https://tacc.tapis.io/v3/tenants/owners/{owner}"
            )
            owner_info = owner_call.json()["result"]

            tenant = build_tenant_model(tenant_info, owner_info)

            tenants.append(tenant)
    except Exception as e:
        logger.error(e)

    return tenants


def generate_overview_data(tenant: str = '', start_date=None, end_date=None, get_issues: bool = False):
    overview = {}
    try:
        auth_data = get_auth_data(tenant)
        logger.debug(auth_data)

        if tenant == 'tapis':
            tenants = get_tenants()
            auth_data['total_num_tenants'] = len(tenants)

        overview['auth_data'] = auth_data
    except Exception as e:
        logger.error(f"Error getting auth data: {e}")

    try:
        jobs_data = get_jobs_data(tenant)
        overview['jobs_data'] = jobs_data
    except Exception as e:
        logger.error(f"Error getting jobs data: {e}")

    if tenant == 'tacc' or tenant == 'tapis':
        try:
            streams_data = {}
            all_streams_data = get_streams_data(tenant)
            for stream_data in all_streams_data:
                streams_data['amount_data_streamed'] = streams_data.get(
                    'amount_data_streamed', 0) + stream_data['amount_data_streamed']
                streams_data['number_data_streams'] = streams_data.get(
                    'number_data_streams', 0) + stream_data['number_data_streams']
                streams_data['number_archives_registered'] = streams_data.get(
                    'number_archives_registered', 0) + stream_data['number_archives_registered']

            overview['streams_data'] = streams_data
        except Exception as e:
            logger.error(f"Error getting streams data: {e}")

    if tenant == 'tapis':
        try:
            misc_data = {}
            # trainings_url = requests.get(
            #     "https://raw.githubusercontent.com/tapis-project/tapis-reporting/main/tapis_training.json"
            # )

            # trainings_data = trainings_url.json()
            misc_data['total_trainings'] = Training.objects.count()
            misc_data['total_github_issues'] = None
            misc_data['num_research_papers'] = Paper.objects.count()

            if get_issues:
                total_github_issues = 0
                repos = get_repos("tapis-project")
                for repo in repos:
                    total_github_issues += repo['total_issues']
                misc_data['total_github_issues'] = total_github_issues

            overview['misc_data'] = misc_data
        except Exception as e:
            logger.error(f"Error getting misc data: {e}")

    return overview
