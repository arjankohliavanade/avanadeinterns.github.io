from django.contrib import admin
from .models import ExternalPatient,EventType

# Register your models here.
admin.site.register(ExternalPatient)
admin.site.register(EventType)