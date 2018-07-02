from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, render_to_response
from django.views.generic import ListView
from django.utils import timezone
from django_tables2 import RequestConfig
from .models import ExternalPatient,TimedEvent,PatientVisit,EventType, ExternalPatientFilter, PatientVisitFilter
from .tables import External_Patient_Table,Timed_Event_Table, Patient_Visit_Table
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin
import json
from collections import OrderedDict

def summary_chart(request):

    categories = ['Timed Events']
    series = get_average_timed_events()

    # to json for javascript on the client side
    categories = json.dumps(categories)
    series = json.dumps(series)
    return render(request, 'summary_chart.html', {'categories':categories, 'series':series})

def index(request):
    return HttpResponse("Hello World to All!")

class PatientList(ListView):
    model = ExternalPatient
    template_name = 'patient_list.html'

# Search for external patients
class FilteredPatientListView(SingleTableMixin, FilterView):
    table_class = External_Patient_Table
    model = ExternalPatient
    template_name = 'external_patient_list.html'
    filterset_class = ExternalPatientFilter

# Search for patient visit
class FilteredVisitListView(SingleTableMixin, FilterView):
    table_class = Patient_Visit_Table
    model = PatientVisit
    template_name = 'patient_visit_list.html'
    filterset_class = PatientVisitFilter

def external_patient(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login/')

    table = External_Patient_Table(ExternalPatient.objects.all())
    RequestConfig(request).configure(table)
    return render(request, 'external_patient_list.html', {'table' : table})

# Post start time
def timed_event_start(request, timed_event_id):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login/')

    timed_event = TimedEvent.objects.get(id=timed_event_id)
    external_patient_id = timed_event.patient_visit.external_patient.id
    timed_event.stop = None
    timed_event.start = timezone.now()
    timed_event.auth_user_id = request.user.id
    timed_event.save()
    # Redirect to stay on same page
    return HttpResponseRedirect('/todays_timed_events/' + str(external_patient_id))

# Post stop time
def timed_event_stop(request, timed_event_id):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login/')

    timed_event = TimedEvent.objects.get(id=timed_event_id)
    external_patient_id = timed_event.patient_visit.external_patient.id
    right_now = timezone.now()
    if timed_event.start:
        timed_event.stop = right_now
        timed_event.save()

    # If checking out (overall), then stop all timed events that have been started, and delete unused events
    # that were never started
    if overall_timed_event(timed_event):
        visits_timed_events = TimedEvent.objects.filter(patient_visit_id=timed_event.patient_visit_id)
        for visits_timed_event in visits_timed_events:
            if visits_timed_event.start:
                if not visits_timed_event.stop:
                    visits_timed_event.stop = right_now
                    visits_timed_event.save()
            else:
                # Delete unused events that were never started
                visits_timed_event.delete()

    return HttpResponseRedirect('/todays_timed_events/' + str(external_patient_id))

def todays_timed_events(request, external_patient_id):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login/')

    this_patients_visits = PatientVisit.objects.filter(external_patient_id=external_patient_id)
    the_patient_visit = None
    today = timezone.now().date()
    for patient_visit in this_patients_visits:
        visit_date = patient_visit.visit_date
        if visit_date == today:
            the_patient_visit = patient_visit
            break

    if not the_patient_visit:
        the_patient_visit = PatientVisit(external_patient_id=external_patient_id, visit_date=timezone.now().date())
        the_patient_visit.save()

    data = get_todays_timed_events(request, the_patient_visit)
    external_patient_fullname_dob = the_patient_visit.external_patient.first_name + ' ' + \
                                     the_patient_visit.external_patient.last_name + ' : ' + \
                                    the_patient_visit.external_patient.date_of_birth.strftime('%m/%d/%Y')
    table = Timed_Event_Table(data=data)
    RequestConfig(request).configure(table)
    return render(request, 'timed_event_list.html', {'table' : table, \
                                                     'external_patient_fullname_dob' : external_patient_fullname_dob})

def patient_visits(request, external_patient_id):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login/')

    try:
        external_patient = ExternalPatient.objects.get(id=external_patient_id)
    except:
        return HttpResponseRedirect('/patients/')

    data = get_patient_visits(request, external_patient_id)
    external_patient_fullname_dob = external_patient.first_name + ' ' + \
                                    external_patient.last_name + ' : ' + \
                                    external_patient.date_of_birth.strftime('%m/%d/%Y')
    table = Patient_Visit_Table(data=data)
    RequestConfig(request).configure(table)
    return render(request, 'patient_visit_list.html', {'table' : table, \
                                                     'external_patient_fullname_dob' : external_patient_fullname_dob})

def get_todays_timed_events(request, the_patient_visit):
    data = []
    all_event_types = EventType.objects.all()

    # Unless the patient_visit is checked out, make sure a timed_event exists for every event type
    if patient_visit_checked_out(the_patient_visit):
        timed_events = TimedEvent.objects.filter(patient_visit_id=the_patient_visit.id)
    else:
        timed_events = []
        for event_type in all_event_types.iterator():
            try:
                timed_event = TimedEvent.objects.get(event_type_id=event_type.id, patient_visit_id=the_patient_visit.id)
            except:
                timed_event = TimedEvent(patient_visit_id=the_patient_visit.id, \
                                         event_type_id=event_type.id, auth_user_id=request.user.id)
                if overall_timed_event(timed_event):
                    timed_event.start = timezone.now()
                timed_event.save()
            timed_events.append(timed_event)

    for timed_event in timed_events:
        d = {}
        d['id'] = timed_event.id
        d['Event'] = timed_event.event_type.name
        d['Started At'] = timed_event.start
        d['Stopped At'] = timed_event.stop
        d['User'] = timed_event.auth_user.username
        if patient_visit_checked_out(the_patient_visit):
            d['start_action'] = ''
            d['stop_action'] = ''
        elif overall_timed_event(timed_event):
            d['start_action'] = 'Restart Now'
            d['stop_action'] = 'Check Out'
        else:
            d['start_action'] = 'Restart Now' if timed_event.start else 'Start Now'
            d['stop_action'] = 'Stop Now' if timed_event.start else ''

        data.append(d)
    return data

# Get history of patient visit's timed events
def get_patient_visits(request, external_patient_id):
    data = []
    patient_visits = PatientVisit.objects.filter(external_patient_id=external_patient_id).order_by('-visit_date')
    for patient_visit in patient_visits.iterator():
        for timed_event in TimedEvent.objects.filter(patient_visit=patient_visit).order_by('id'):
            d = {}
            d['Visit Date'] = patient_visit.visit_date
            d['Event'] = timed_event.event_type.name
            d['Started At'] = timed_event.start
            d['Stopped At'] = timed_event.stop
            d['User'] = timed_event.auth_user.username
            data.append(d)
    return data

def overall_timed_event(timed_event):
    return 'overall' in timed_event.event_type.name.lower()

def overall_timed_event_expired(timed_event):
    return overall_timed_event(timed_event) and timed_event.start and timed_event.stop

def patient_visit_checked_out(the_patient_visit):
    timed_events = TimedEvent.objects.filter(patient_visit_id=the_patient_visit.id)
    for timed_event in timed_events:
        if overall_timed_event_expired(timed_event):
            return True
    return False

def get_todays_timed_events(request, the_patient_visit):
    data = []
    all_event_types = EventType.objects.all()

    # Unless the patient_visit is checked out, make sure a timed_event exists for every event type
    if patient_visit_checked_out(the_patient_visit):
        timed_events = TimedEvent.objects.filter(patient_visit_id=the_patient_visit.id)
    else:
        timed_events = []
        for event_type in all_event_types.iterator():
            try:
                timed_event = TimedEvent.objects.get(event_type_id=event_type.id, patient_visit_id=the_patient_visit.id)
            except:
                timed_event = TimedEvent(patient_visit_id=the_patient_visit.id, \
                                         event_type_id=event_type.id, auth_user_id=request.user.id)
                if overall_timed_event(timed_event):
                    timed_event.start = timezone.now()
                timed_event.save()
            timed_events.append(timed_event)

    for timed_event in timed_events:
        d = {}
        d['id'] = timed_event.id
        d['Event'] = timed_event.event_type.name
        d['Started At'] = timed_event.start
        d['Stopped At'] = timed_event.stop
        d['User'] = timed_event.auth_user.username
        if patient_visit_checked_out(the_patient_visit):
            d['start_action'] = ''
            d['stop_action'] = ''
        elif overall_timed_event(timed_event):
            d['start_action'] = 'Restart Now'
            d['stop_action'] = 'Check Out'
        else:
            d['start_action'] = 'Restart Now' if timed_event.start else 'Start Now'
            d['stop_action'] = 'Stop Now' if timed_event.start else ''

        data.append(d)
    return data

# Get history of patient visit's timed events
def get_patient_visits(request, external_patient_id):
    data = []
    patient_visits = PatientVisit.objects.filter(external_patient_id=external_patient_id).order_by('-visit_date')
    for patient_visit in patient_visits.iterator():
        for timed_event in TimedEvent.objects.filter(patient_visit=patient_visit).order_by('id'):
            d = {}
            d['Visit Date'] = patient_visit.visit_date
            d['Event'] = timed_event.event_type.name
            d['Started At'] = timed_event.start
            d['Stopped At'] = timed_event.stop
            d['User'] = timed_event.auth_user.username
            data.append(d)
    return data

def overall_timed_event(timed_event):
    return 'overall' in timed_event.event_type.name.lower()

def overall_timed_event_expired(timed_event):
    return overall_timed_event(timed_event) and timed_event.start and timed_event.stop

def patient_visit_checked_out(the_patient_visit):
    timed_events = TimedEvent.objects.filter(patient_visit_id=the_patient_visit.id)
    for timed_event in timed_events:
        if overall_timed_event_expired(timed_event):
            return True
    return False

def get_average_timed_events():
    # series = [{ 'name': 'John', 'data': [1, 0, 4]},
    #             { 'name': 'King', 'data': [5, 7, 3]}]

    names = OrderedDict()
    event_types = EventType.objects.all()
    for event_type in event_types:
        sum_seconds = 0
        legit_count = 0
        timed_events = TimedEvent.objects.filter(event_type_id=event_type.id)
        for timed_event in timed_events:
            # ignore timed_events that don't have a start and stop
            if timed_event.start and timed_event.stop:
                legit_count += 1
                elapsed_time = timed_event.stop - timed_event.start
                sum_seconds += elapsed_time.total_seconds()

        # don't divide by 0
        if legit_count == 0:
            average_minutes = 0
        else:
            average_minutes = sum_seconds / 60 / legit_count

        average_minutes = "{0:.1f}".format(average_minutes)
        names[event_type.name] = [float(average_minutes)]
    series = []
    for name in names:
        series.append({'name':name, 'data':names[name]})
    return series
