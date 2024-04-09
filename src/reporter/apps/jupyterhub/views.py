"""Logging required for logging purposes"""
import logging
from itertools import chain
import random

from django.http import HttpResponse
from django.template import loader
from django.contrib.auth.decorators import login_required
from .models import FileLog, LoginLog
from ..main.models import Tenant


logger = logging.getLogger(__name__)

# Create your views here.


@login_required
def index(request):
    """
    Handles default path of JupyterHub service
    """
    if request.method == "GET":
        template = loader.get_template("jupyterhub/index.html")

        context = {
            "error": False,
        }

        return HttpResponse(template.render(context, request))

    elif request.method == "POST":
        template = loader.get_template("jupyterhub/index.html")
        logger.debug("POST index")

        context = {
            "error": False,
        }

        logger.debug(request.POST)
        try:
            start_date = request.POST.get("start_date")
            end_date = request.POST.get("end_date")
            tenant = request.POST.get("tenant")

            accessed_files = FileLog.objects.filter(
                tenant=tenant, date__range=(start_date, end_date)
            )
            logger.debug(accessed_files)

            login_users = LoginLog.objects.filter(
                tenant=tenant, date__range=(start_date, end_date)
            )
            logger.debug(login_users)

            tenant_obj = Tenant.objects.get(pk=tenant)

            directories, counts = get_directory_counts(
                tenant_obj, accessed_files.values('filepath'))

            labels = []
            dir_counts = []
            for dir in directories:
                labels.append(dir)
            for count in counts:
                dir_counts.append(count)

            background_colors = get_background_colors(dir_counts)
            logger.debug(background_colors)

            created_files = accessed_files.filter(action="created")
            opened_files = accessed_files.filter(action="opened")
            num_created_files = created_files.count()
            num_opened_files = opened_files.count()

            unique_login_count = login_users.values(
                "user").distinct().count()
            total_login_count = login_users.count()

            try:
                combined = list(chain(accessed_files, login_users))
                logger.debug(combined)
                users = []
                for log in combined:
                    users.append(log.user)
                logger.debug(users)
                unique_users = set(users)
                total_user_count = len(unique_users)

                data = {
                    'num_created_files': num_created_files,
                    'num_opened_files': num_opened_files,
                    'unique_login_count': unique_login_count,
                    'total_login_count': total_login_count,
                    'total_user_count': total_user_count
                }
                context['data'] = data
                context['labels'] = labels
                context['directories'] = dir_counts
                context['backgroundColors'] = background_colors
                logger.debug(context)
            except Exception as e:
                logger.debug(e)
                context["error"] = True
                context["message"] = e

        except Exception as e:
            context["error"] = True
            context["message"] = e
            logger.debug(e)

        return HttpResponse(template.render(context, request))


@login_required
def users(request):
    """
    Handles user access data of JupyterHub service
    """
    if request.method == "GET":
        template = loader.get_template("jupyterhub/users.html")

        context = {
            "error": False,
        }

        return HttpResponse(template.render(context, request))

    elif request.method == "POST":
        template = loader.get_template("jupyterhub/users.html")

        context = {
            "error": False,
        }

        tenant = request.POST.get("tenant")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")

        query = LoginLog.objects.filter(
            tenant=tenant, date__range=(start_date, end_date)
        ).order_by("date")

        context["user_access"] = query

        return HttpResponse(template.render(context, request))


@login_required
def files(request):
    """
    Handles default path of JupyterHub service
    """
    if request.method == "GET":
        template = loader.get_template("jupyterhub/files.html")

        context = {
            "error": False,
        }

        return HttpResponse(template.render(context, request))

    elif request.method == "POST":
        template = loader.get_template("jupyterhub/files.html")

        context = {
            "error": False,
        }

        tenant = request.POST.get("tenant")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")

        query = FileLog.objects.filter(
            tenant=tenant, date__range=(start_date, end_date)
        ).order_by("date")

        context["file_access"] = query

        return HttpResponse(template.render(context, request))


@login_required
def dirs(request):
    """
    Handles default path of JupyterHub service
    """
    if request.method == "GET":
        template = loader.get_template("jupyterhub/dirs.html")

        context = {
            "error": False,
        }

        return HttpResponse(template.render(context, request))

    elif request.method == "POST":
        template = loader.get_template("jupyterhub/dirs.html")

        context = {
            "error": False,
        }

        tenant = request.POST.get("tenant")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")

        accessed_files = FileLog.objects.filter(
            tenant=tenant, date__range=(start_date, end_date)
        )
        directories_accessed = get_directories(
            accessed_files.values("filepath")
        )

        context["dir_access"] = directories_accessed

        return HttpResponse(template.render(context, request))


def get_directories(accessed_files):
    filepaths = list(accessed_files)
    logger.debug(f"Filepaths: {filepaths}")
    dir_counts = {}

    for path in filepaths:
        dir = path["filepath"]
        dir_counts[dir] = dir_counts.get(dir, 0) + 1

    dirs = []
    for path in dir_counts.keys():
        dir = path
        count = dir_counts[path]
        dir_count = {"directory": dir, "count": count}
        dirs.append(dir_count)

    dirs = sorted(dirs, key=lambda d: d["count"], reverse=True)

    return dirs


def get_directory_counts(tenant, accessed_files):
    filepaths = list(accessed_files)
    dir_counts = {}
    directories = get_tenant_directories(tenant)

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


def get_tenant_directories(tenant):
    temp_directories = tenant.tenantdirectory_set.all().values('directory')
    tenant_directories = []

    for dir in list(temp_directories):
        tenant_directories.append(dir['directory'])

    return tenant_directories


def get_background_colors(data):
    color = ["#"+''.join([random.choice('0123456789ABCDEF')
                          for j in range(6)]) for i in range(len(data))]
    return color
