from django.urls import path, re_path

from . import views

app_name = 'sesar_api'

urlpatterns = [
    re_path('auth/' + r'login/(?P<backend>[^/]+)/$', views.login_by_access_token),
    path('auth/user/', views.user_details),
    path('auth/logout/', views.revoke_access_token),
    path('organization/<str:name>/', views.view_organization),
    path('organization/user-membership/', views.view_user_organizations),
    path('organization/create/', views.create_organization),
    path('organization/update/<int:pk>', views.update_organization),
    path('organization/deactivate/<int:pk>', views.deactivate_organization),
    path('organization/transfer/<int:pk>', views.transfer_organization),
]