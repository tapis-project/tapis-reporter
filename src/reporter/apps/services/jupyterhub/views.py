"""Logging required for logging purposes"""
import logging
from itertools import chain

from django.http import HttpResponse
from django.template import loader
from django.contrib.auth.decorators import login_required
from .models import FileLog, LoginLog


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

        context = {
            "error": False,
        }
        try:
            start_date = request.POST.get("start_date")
            end_date = request.POST.get("end_date")
            tenant = request.POST.get("tenant")
            query = ""
            if "file_logs" in request.POST:
                context["file_logs"] = True
                query = FileLog.objects.filter(
                    tenant=tenant, date__range=(start_date, end_date)
                ).order_by("date")

            elif "login_logs" in request.POST:
                query = LoginLog.objects.filter(
                    tenant=tenant, date__range=(start_date, end_date)
                ).order_by("date")

            context["query"] = query
            context["queried"] = True
            if "jhub_stats" in request.POST:
                context["jhub_stats"] = True
                context["queried"] = False
                accessed_files = FileLog.objects.filter(
                    tenant=tenant, date__range=(start_date, end_date)
                )
                directories_accessed = get_directories(
                    accessed_files.values("filepath")
                )
                created_files = accessed_files.filter(action="created")
                opened_files = accessed_files.filter(action="opened")
                num_created_files = created_files.count()
                num_opened_files = opened_files.count()
                login_users = LoginLog.objects.filter(
                    tenant=tenant, date__range=(start_date, end_date)
                )
                unique_login_count = login_users.values("user").distinct().count()
                total_login_count = login_users.count()
                try:
                    combined = list(chain(accessed_files, login_users))
                    users = []
                    for log in combined:
                        users.append(log.user)
                    unique_users = set(users)
                    unique_user_count = len(unique_users)
                except Exception as e:
                    context["error"] = True
                    context["message"] = e
                    unique_user_count = "Error getting unique user count"
                context["num_created_files"] = num_created_files
                context["num_opened_files"] = num_opened_files
                context["unique_login_count"] = unique_login_count
                context["total_login_count"] = total_login_count
                context["unique_user_count"] = unique_user_count
                context["dirs"] = directories_accessed
                context["queried"] = False
        except Exception as e:
            context["error"] = True
            context["message"] = e

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
