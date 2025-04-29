from django.urls import path, re_path
from rest_framework_simplejwt.views import TokenBlacklistView

from .views import *

app_name = 'sesar_api'

urlpatterns = (
    path('sample-metadata', DisplaySampleByIGSNView, name='sampleigsn'),
    path('samples/', get_sample_by_igsn),
)