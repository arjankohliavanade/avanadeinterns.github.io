"""django_project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.generic.base import TemplateView
from medstats.views import external_patient,todays_timed_events,timed_event_stop,\
    timed_event_start, FilteredPatientListView, patient_visits, summary_chart

#
#{% include "navigation.html" %}
#
urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', TemplateView.as_view(template_name='home.html'), name='home'),
    url(r'^patients/$', FilteredPatientListView.as_view(), name='patients'),
    url(r'^patient_visits/([0-9]+)/$', patient_visits, name='patient_visits'),
    url(r'^todays_timed_events/([0-9]+)/$', todays_timed_events, name='todays_timed_events'),
    url(r'^timed_event_start/([0-9]+)/$', timed_event_start, name='timed_event_start'),
    url(r'^timed_event_stop/([0-9]+)/$', timed_event_stop, name='timed_event_stop'),
    url(r'^login/$', auth_views.login, {'template_name': 'login.html'}, name='login'),
    url(r'^logout/$', auth_views.logout, {'template_name': 'logged_out.html'}, name='logout'),
    url(r'^summary_chart/$', summary_chart, name='summary_chart'),


]+static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


