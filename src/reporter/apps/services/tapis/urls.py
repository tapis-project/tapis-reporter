from django.urls import path
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings
from django.conf.urls.static import static

from . import views

app_name = "tapis"
urlpatterns = [
    path("", views.index, name="index"),
    path("tenants/", views.tenants, name="tenants"),
    path("trainings/", views.trainings, name="trainings"),
    path("gateways/", views.gateways, name="gateways"),
    path("gateways/<str:tenant>", views.tenant_gateways, name="tenant_gateways"),
    path("github/", views.github, name="github"),
    path("papers/", views.papers, name="papers"),
    path("streams/", views.streams, name="streams"),
    path("splunk/", views.splunk, name="splunk"),
]
