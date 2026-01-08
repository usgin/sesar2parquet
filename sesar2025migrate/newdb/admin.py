from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Sample)
admin.site.register(SesarUser)
admin.site.register(MaterialType)
admin.site.register(SampleType)
admin.site.register(AgentRoleType)
admin.site.register(SampleMaterial)
admin.site.register(InstitutionType)
admin.site.register(Institution)
admin.site.register(Individual)
admin.site.register(Initiative)
admin.site.register(InitiativeType)
admin.site.register(PlatformType)

