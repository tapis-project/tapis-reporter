import logging

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template import loader

from .models import HazmapperData

logger = logging.getLogger(__name__)

# Create your views here.


@login_required
def index(request):
    if request.method == "GET":
        template = loader.get_template("hazmapper/index.html")

        context = {"error": False}

        try:
            overview_data = generate_overview_data()
            context["user_data"] = overview_data["user_data"]
            context["map_data"] = overview_data["map_data"]
            context["project_data"] = overview_data["project_data"]
        except Exception as e:
            logger.error(f"Error generating overview data: {e}")
            raise Exception

        return HttpResponse(template.render(context, request))


@login_required
def data(request):
    if request.method == "GET":
        template = loader.get_template("hazmapper/data.html")

        context = {"error": False}

        hazmapper_data = [entry for entry in HazmapperData.objects.all()]

        context["hazmapper_data"] = hazmapper_data

        return HttpResponse(template.render(context, request))


def generate_overview_data():
    overview = {}
    try:
        logger.debug("Fetching hazmapper data")
        hazmapper_data = HazmapperData.objects.all()
        user_cnt = HazmapperData.objects.values("user").distinct().count()
        map_cnt = HazmapperData.objects.values("map").distinct().count()
        prj_cnt = HazmapperData.objects.values("project").distinct().count()

        overview["user_data"] = user_cnt
        overview["map_data"] = {
            "num_maps": map_cnt,
            "num_maps_accessed": hazmapper_data.count(),
        }
        overview["project_data"] = prj_cnt

        for entry in hazmapper_data:
            print(entry)
    except Exception as e:
        logger.error(f"Error fertching hazmapper data: {e}")
        raise Exception

    return overview
