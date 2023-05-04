from django.shortcuts import render
from django.template import loader
import os
from django.core.files.storage import default_storage
import glob
from django.conf import settings
from django.contrib.auth.decorators import login_required
import logging
from itertools import chain

logger = logging.getLogger(__name__)

# Create your views here.
from django.http import HttpResponse


@login_required
def index(request):
    return
