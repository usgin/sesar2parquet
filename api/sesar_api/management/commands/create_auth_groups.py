"""
Create permission groups
"""
import logging

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from sesar_api.models import Sample, Group as UserGroup, GroupMember, Permission as SesarPermission
from django.db import IntegrityError

MODELS = ['sample']

GROUPS = [
    {
        'name': 'read_only',
        'permissions': ['view']
    },
    {
        'name': 'read_create',
        'permissions': ['view', 'add']
    },
    {
        'name': 'read_edit',
        'permissions': ['view', 'change']
    },
    {
        'name': 'read_create_edit',
        'permissions': ['view', 'add', 'change']
    },
    {
        'name': 'read_create_edit_deactivate',
        'permissions': ['view', 'add', 'change', 'deactivate']
    },
    {
        'name': 'group_owner',
        'permissions': ['view', 'add', 'change', 'deactivate'],
        'group_permissions': ['add_groupmember', 'change_groupmember', 'delete_groupmember', 'add_group', 'change_group', 'delete_group', 'view_permission', 'add_permission', 'change_permission', 'delete_permission', 'transfer_group_ownership', 'deactivate_group']
    },
    {
        'name': 'group_admin',
        'permissions': ['view', 'add', 'change', 'deactivate'],
        'group_permissions': ['add_groupmember', 'change_groupmember', 'delete_groupmember', 'add_group', 'change_group', 'delete_group', 'view_permission', 'add_permission', 'change_permission', 'delete_permission']
    }
]

# custom permissions for transferring/deactivating groups
NEW_GROUP_PERMISSIONS = [
    {
        'codename': 'transfer_group_ownership',
        'name': 'Can transfer group ownership',
    },
    {
        'codename': 'deactivate_group',
        'name': 'Can deactivate group',
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
            # custom group permissions
            for permission in NEW_GROUP_PERMISSIONS:
                Permission.objects.get_or_create(
                    codename = permission['codename'],
                    name = permission['name'],
                    content_type = ContentType.objects.get_for_model(UserGroup)
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
            if 'group_permissions' in group:
                for codename in group['group_permissions']:
                    try:
                        if 'groupmember' in codename:
                            content_type = ContentType.objects.get_for_model(GroupMember)
                        elif 'group' in codename:
                            content_type = ContentType.objects.get_for_model(UserGroup)
                        elif 'permission' in codename:
                            content_type = ContentType.objects.get_for_model(SesarPermission)
                        permission_to_add = Permission.objects.get(content_type=content_type, codename=codename)
                    except Permission.DoesNotExist:
                        logging.warning("Permission not found with codename '{}'.".format(codename))
                        continue

                    new_group.permissions.add(permission_to_add)
            

        print("Created default groups and permissions.")