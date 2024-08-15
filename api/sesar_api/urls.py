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
    path('organization/update/', views.update_organization),
    path('organization/deactivate/', views.deactivate_organization),
    path('organization/transfer/', views.transfer_organization),
    path('organization/<str:name>/members/', views.view_organization_members),
    path('organization/members/create/', views.create_organization_member),
    path('organization/members/update/', views.update_organization_member),
    path('organization/members/delete/', views.delete_organization_member),
    path('organization/<str:name>/teams/', views.view_organization_teams),
    path('organization/<str:organization>/teams/<str:team>/', views.view_organization_team),
    path('organization/teams/create/', views.create_organization_team),
    path('organization/teams/update/', views.update_organization_team),
    path('organization/teams/delete/', views.delete_organization_team),
    path('organization/teams/add-member/', views.add_organization_team_member),
    path('organization/teams/remove-member/', views.remove_organization_team_member),
]