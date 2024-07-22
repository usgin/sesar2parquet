"""
Create permission groups
"""
import logging

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from sesar_api.models import Sample
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
]


class Command(BaseCommand):
    help = 'Creates default permission groups'
       

    def handle(self, *args, **options):
        # add a custom permission for sample deactivation
        try:
            content_type = ContentType.objects.get_for_model(Sample)
            permission = Permission.objects.create(
                codename="deactivate_sample",
                name="Can deactivate sample",
                content_type=content_type,
            )
        except IntegrityError:
            print('Deactivate sample permission already exists.')

        for group in GROUPS:
            new_group, created = Group.objects.get_or_create(name=group['name'])
            for model in MODELS:
                for permission in group['permissions']:
                    name = 'Can {} {}'.format(permission, model)
                    print("Creating {}".format(name))

                    try:
                        permission_to_add = Permission.objects.get(name=name)
                    except Permission.DoesNotExist:
                        logging.warning("Permission not found with name '{}'.".format(name))
                        continue

                    new_group.permissions.add(permission_to_add)
            

        print("Created default group and permissions.")