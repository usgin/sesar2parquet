from django.urls import path, re_path

from . import views

app_name = 'sesar_api'

urlpatterns = [
    re_path('auth/' + r'login/(?P<backend>[^/]+)/$', views.login_by_access_token),
    path('auth/user/', views.user_details),
    path('auth/logout/', views.revoke_access_token),
]