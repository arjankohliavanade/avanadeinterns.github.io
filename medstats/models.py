from django.db import models
import django_filters

class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=80)

    class Meta:
        managed = False
        db_table = 'auth_group'


# class AuthGroupPermissions(models.Model):
#     group = models.ForeignKey(AuthGroup)
#     permission = models.ForeignKey('AuthPermission')
#
#     class Meta:
#         managed = False
#         db_table = 'auth_group_permissions'
#         unique_together = (('group_id2', 'permission_id'),)
#
#
# class AuthPermission(models.Model):
#     name = models.CharField(max_length=255)
#     content_type = models.ForeignKey('DjangoContentType')
#     codename = models.CharField(max_length=100)
#
#     class Meta:
#         managed = False
#         db_table = 'auth_permission'
#         unique_together = (('content_type_id', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=30)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'

class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', blank=True, null=True)
    user = models.ForeignKey(AuthUser)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class EventType(models.Model):
    name = models.CharField(max_length=128, blank=True, null=True)
    description = models.CharField(max_length=512, blank=True, null=True)
    flow_order = models.IntegerField(default=0, null=False)

    class Meta:
        managed = False
        db_table = 'event_type'
        ordering = ['flow_order']
    def __str__(self):
        return self.name


class ExternalPatient(models.Model):
    last_name = models.CharField(max_length=128, blank=True, null=True)
    first_name = models.CharField(max_length=128, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'external_patient'
        ordering = ['last_name', 'first_name']
    def __str__(self):
        return self.last_name + ', ' + self.first_name

# Search for external patient
class ExternalPatientFilter(django_filters.FilterSet):
    class Meta:
        model = ExternalPatient
        fields = ['last_name','first_name']
        filter_overrides = {
            models.CharField : {
                'filter_class':django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
        }

class PatientVisit(models.Model):
    external_patient = models.ForeignKey(ExternalPatient, models.DO_NOTHING, blank=True, null=True)
    visit_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'patient_visit'
        ordering = ['visit_date']
    def __str__(self):
        return self.visit_date

# Search for patient visit
class PatientVisitFilter(django_filters.FilterSet):
    class Meta:
        model = PatientVisit
        fields = ['visit_date']
        filter_overrides = {
            models.DateField: {
                'filter_class': django_filters.DateFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
        }

class TimedEvent(models.Model):
    patient_visit = models.ForeignKey(PatientVisit, models.DO_NOTHING, blank=True, null=True)
    event_type = models.ForeignKey(EventType, models.DO_NOTHING, blank=True, null=True)
    start = models.DateTimeField(blank=True, null=True)
    stop = models.DateTimeField(blank=True, null=True)
    auth_user = models.ForeignKey(AuthUser, models.DO_NOTHING, blank=True, null=True)
    notes = models.CharField(max_length=512, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'timed_event'
        ordering = ['id']



