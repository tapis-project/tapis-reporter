from django.urls import path

from . import views

app_name = "jupyterhub"
urlpatterns = [
    path("", views.index, name="index"),
    path("users/", views.users, name="users"),
    path("files/", views.files, name="files"),
    path("dirs/", views.dirs, name="dirs"),
]
