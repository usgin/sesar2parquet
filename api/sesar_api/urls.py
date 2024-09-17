from django.urls import path, re_path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from . import views

app_name = 'sesar_api'

urlpatterns = [
    re_path('auth/' + r'login/(?P<backend>[^/]+)/$', views.login_by_access_token),
    path('auth/user/', views.user_details),
    path('auth/logout/', views.revoke_access_token),
    path("auth/token/", views.get_jwt_for_user, name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path('group/<str:name>/', views.view_group),
    path('group/user-membership/', views.view_user_groups),
    path('group/create/', views.create_group),
    path('group/update/', views.update_group),
    path('group/deactivate/', views.deactivate_group),
    path('group/transfer/', views.transfer_group),
    path('group/<str:name>/members/', views.view_group_members),
    path('group/members/create/', views.create_group_member),
    path('group/members/update/', views.update_group_member),
    path('group/members/delete/', views.delete_group_member),
    path('group/<str:name>/teams/', views.view_group_teams),
    path('group/<str:group>/teams/<str:team>/', views.view_group_team),
    path('group/teams/create/', views.create_group_team),
    path('group/teams/update/', views.update_group_team),
    path('group/teams/delete/', views.delete_group_team),
    path('group/teams/add-member/', views.add_group_team_member),
    path('group/teams/remove-member/', views.remove_group_team_member),
]