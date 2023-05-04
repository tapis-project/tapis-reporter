from django.urls import path
from . import views

app_name = 'auth'
urlpatterns = [
    path('logged-out', views.logged_out, name='logout'),
    path('tapisauth', views.tapis_oauth, name='tapis_oauth'),
    path('tapisauth/session-error', views.tapis_session_error, name='tapis_session_error'),
    path('tapis3/callback', views.tapis_oauth_callback, name='tapis_oauth_callback'),
]
