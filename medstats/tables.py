import django_tables2 as tables
from .models import ExternalPatient,TimedEvent, PatientVisit
from django_tables2.utils import A

class External_Patient_Table(tables.Table):

    #timed_events = tables.TemplateColumn('<a href="/timed_events/{{record.id}}">Timed Events</a>', orderable=False)
    patient_visits = tables.LinkColumn(verbose_name='# Visits', viewname='patient_visits', text=lambda record: \
                                    External_Patient_Table.number_of_patient_visits(record), args=[A('id')], \
                                     orderable=False, empty_values=())
    todays_visit = tables.LinkColumn(verbose_name='Today\'s Visit', viewname='todays_timed_events', text=lambda record: \
                                    External_Patient_Table.get_todays_visit_link_text(record), args=[A('id')], \
                                     orderable=False, empty_values=())
    class Meta:
        model = ExternalPatient
        template_name = 'django_tables2/bootstrap.html'
        fields = ('last_name', 'first_name', 'date_of_birth', 'patient_visits', 'todays_visit')

    @staticmethod
    def number_of_patient_visits(record):
        count = PatientVisit.objects.filter(external_patient_id=record.id).count()
        return count if count > 0 else ''

    @staticmethod
    def get_todays_visit_link_text(record):
        patient_visit_queryset = PatientVisit.objects.filter(external_patient_id=record.id)
        for patient_visit in patient_visit_queryset:
            date = patient_visit.visit_date
            today = date.today()
            if date == today:
                return 'View'
        return 'Check In'

class Timed_Event_Table(tables.Table):
    tables.Column(verbose_name='Event')
    tables.Column(verbose_name='Started At')
    tables.Column(verbose_name='Stopped At')
    tables.Column(verbose_name='User')
    start_action = tables.LinkColumn(verbose_name='Start Action', viewname='timed_event_start', text=lambda data: \
        data['start_action'], args=[A('id')], orderable=False, empty_values=())
    stop_action = tables.LinkColumn(verbose_name='Stop Action', viewname='timed_event_stop', text=lambda data: \
        data['stop_action'], args=[A('id')], orderable=False, empty_values=())
    class Meta:
        model = TimedEvent
        template_name = 'django_tables2/bootstrap.html'
        fields = ('Event', 'Started At', 'Stopped At', 'User')

class Patient_Visit_Table(tables.Table):
    tables.Column(verbose_name='Visit Date')
    tables.Column(verbose_name='Event')
    tables.Column(verbose_name='Started At')
    tables.Column(verbose_name='Stopped At')
    tables.Column(verbose_name='User')

    class Meta:
        model = TimedEvent
        template_name = 'django_tables2/bootstrap.html'
        fields = ('Visit Date','Event', 'Started At', 'Stopped At', 'User')

