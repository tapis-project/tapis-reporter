from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template import loader


@login_required
def index(request):
    template = loader.get_template("main/index.html")
    context = {}
    return HttpResponse(template.render(context, request))
