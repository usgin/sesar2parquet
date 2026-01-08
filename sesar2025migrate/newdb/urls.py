from django.urls import path
from .views import *

urlpatterns = (
    path('', IndexPageView, name='index'),
    path('indivdiuals', DisplayIndividualsView, name='individual'),
    path('institutions', DisplayInstitutionView, name='institutions'),
    path('sesarusers', DisplaySesarUserView, name='sesarusers'),
    path('sampleigsn', DisplaySampleByIGSNView, name='sampleigsn'),
    path('sampleigsnjson', isamplesJSONByIGSNView, name='sampleigsnjson'),
    path('platformtypes', DisplayPlatformTypeView, name='platformtypes'),
    path('collectorsamples', DisplaySampleByCollectorView, name='collectorsamples')
)