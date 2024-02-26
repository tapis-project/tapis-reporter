from django.urls import path
from . import views

app_name = "jupyterhub"
urlpatterns = [
    path("", views.index, name="index"),
]
