from django.urls import path, re_path
from rest_framework_simplejwt.views import TokenBlacklistView
from sesar_api.views import CustomTokenRefreshView

from . import views

app_name = 'sesar_api'

urlpatterns = [
    re_path('auth/' + r'login/(?P<backend>[^/]+)/$', views.login_by_access_token),
    path('auth/user/', views.user_details),
    path('auth/logout/', views.revoke_access_token),
    path("auth/token/", views.get_jwt_for_user, name="token_obtain_pair"),
    path("auth/token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path('auth/token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),
    path('auth/token/blacklist-all/', views.revoke_all_jwt_for_user),
    path("auth/token/<str:connection>/", views.get_jwt_for_user_with_connection),
    path('team/search/', views.search_teams),
    path('team/create/', views.create_team),
    path('team/user-membership/', views.view_user_teams),
    path('team/update/', views.update_team),
    path('team/deactivate/', views.deactivate_team),
    path('team/transfer/', views.transfer_team),
    path('team/<str:name>/', views.view_team),
    path('team/<str:name>/samples/', views.view_user_team_samples),
    path('team/<str:name>/members/', views.view_team_members),
    path('team/<str:name>/permissions/', views.view_team_permissions),
    path('team/<str:name>/usercodes/', views.view_team_user_codes),
    path('team/members/create/', views.create_team_member),
    path('team/members/update/', views.update_team_member),
    path('team/members/delete/', views.delete_team_member),
    path('team/members/accept-invitation/', views.accept_invitation),
    path('team/members/decline-invitation/', views.decline_invitation),
    path('user/search/', views.search_users),
    path('usercode/', views.view_user_user_codes),
    path('usercode/create/', views.create_user_code),
    path('usercode/delete/', views.delete_user_code),
    path('usercode/<str:user_code>/', views.view_user_code),
    path('permissions/create/', views.create_permission),
    path('permissions/update/', views.update_permission),
    path('permissions/delete/', views.delete_permission),
    path('transfer/', views.view_transfers),
    path('transfer/create/', views.create_transfer),
    path('transfer/update/', views.update_transfer),
    path('statistics/igsns/count/', views.get_published_sample_count),
    path('statistics/igsns/count/parent/', views.get_published_parent_sample_count),
    path('statistics/igsns/count/sample-type/', views.get_sample_count_by_sample_type),
    path('statistics/igsns/count/institution/', views.get_sample_count_by_institution),
    path('sitemap/', views.get_igsn_list_for_sitemap),
    path('sample/igsn-ev-json-ld/', views.get_sample_jsonld),
]