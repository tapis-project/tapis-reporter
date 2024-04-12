"""Logging required for logging purposes"""
import logging

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template import loader

logger = logging.getLogger(__name__)

# Create your views here.


@login_required
def index(request):
    """
    Handles default path of JupyterHub service
    """
    if request.method == "GET":
        template = loader.get_template("hazmapper/index.html")

        context = {"error": False}

        return HttpResponse(template.render(context, request))
