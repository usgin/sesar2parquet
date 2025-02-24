"""
Create permission groups
"""
import logging

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from sesar_api.models import Sample, Team, TeamMember, Permission as SesarPermission, SesarUserCode
from django.db import IntegrityError

MODELS = ['sample']

GROUPS = [
    {
        'name': 'Read Only',
        'permissions': ['view']
    },
    {
        'name': 'Read Create',
        'permissions': ['view', 'add']
    },
    {
        'name': 'Read Edit',
        'permissions': ['view', 'change']
    },
    {
        'name': 'Read Create Edit',
        'permissions': ['view', 'add', 'change']
    },
    {
        'name': 'Read Create Edit Deactivate',
        'permissions': ['view', 'add', 'change', 'deactivate']
    },
    {
        'name': 'Team Owner',
        'permissions': ['view', 'add', 'change', 'deactivate', 'transfer'],
        'team_permissions': ['add_teammember', 'change_teammember', 'delete_teammember', 'add_team', 'change_team', 'delete_team', 'view_permission', 'add_permission', 'change_permission', 'delete_permission', 'transfer_team_ownership', 'deactivate_team', 'add_sesarusercode', 'delete_sesarusercode']
    },
    {
        'name': 'Team Admin',
        'permissions': ['view', 'add', 'change', 'deactivate', 'transfer'],
        'team_permissions': ['add_teammember', 'change_teammember', 'delete_teammember', 'add_team', 'change_team', 'delete_team', 'view_permission', 'add_permission', 'change_permission', 'delete_permission', 'add_sesarusercode', 'delete_sesarusercode']
    }
]

# custom permissions for transferring/deactivating teams
NEW_TEAM_PERMISSIONS = [
    {
        'codename': 'transfer_team_ownership',
        'name': 'Can transfer team ownership',
    },
    {
        'codename': 'deactivate_team',
        'name': 'Can deactivate team',
    },
]

class Command(BaseCommand):
    help = 'Creates default permission groups'
       

    def handle(self, *args, **options):
        # add a custom permissions
        try:
            # custom permission for sample deactivation
            Permission.objects.get_or_create(
                codename = "deactivate_sample",
                name = "Can deactivate sample",
                content_type = ContentType.objects.get_for_model(Sample)
            )
            Permission.objects.get_or_create(
                codename = "transfer_sample",
                name = "Can transfer sample",
                content_type = ContentType.objects.get_for_model(Sample)
            )
            # custom team permissions
            for permission in NEW_TEAM_PERMISSIONS:
                Permission.objects.get_or_create(
                    codename = permission['codename'],
                    name = permission['name'],
                    content_type = ContentType.objects.get_for_model(Team)
                )
        except IntegrityError:
            print('Custom permission already exists.')

        for group in GROUPS:
            new_group, created = Group.objects.get_or_create(name=group['name'])
            for model in MODELS:
                for permission in group['permissions']:
                    codename = '{}_{}'.format(permission, model)
                    try:
                        permission_to_add = Permission.objects.get(codename=codename)
                    except Permission.DoesNotExist:
                        logging.warning("Permission not found with codename '{}'.".format(codename))
                        continue

                    new_group.permissions.add(permission_to_add)
            if 'team_permissions' in group:
                for codename in group['team_permissions']:
                    try:
                        if 'teammember' in codename:
                            content_type = ContentType.objects.get_for_model(TeamMember)
                        elif 'team' in codename:
                            content_type = ContentType.objects.get_for_model(Team)
                        elif 'permission' in codename:
                            content_type = ContentType.objects.get_for_model(SesarPermission)
                        elif 'sesarusercode' in codename:
                            content_type = ContentType.objects.get_for_model(SesarUserCode)
                        permission_to_add = Permission.objects.get(content_type=content_type, codename=codename)
                    except Permission.DoesNotExist:
                        logging.warning("Permission not found with codename '{}'.".format(codename))
                        continue

                    new_group.permissions.add(permission_to_add)
            

        print("Created default groups and permissions.")