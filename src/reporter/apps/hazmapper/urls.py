from django.urls import path

from . import views

app_name = "hazmapper"
urlpatterns = [
    path("", views.index, name="index"),
    path("data/", views.data, name="data"),
    # path("projects/", views.projects, name="projects"),
]
