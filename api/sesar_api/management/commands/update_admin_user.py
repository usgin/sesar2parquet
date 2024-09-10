import os
import sys

from django.core.management.base import BaseCommand, CommandError
from sesar_api.models import User
from django.conf import settings


class Command(BaseCommand):
    help = 'Creates the initial admin user, or updates the password to reflect the latest value'

    def create_or_update_admin(self):
        admin_user=User.objects.filter(username=os.getenv('DJANGO_ADMIN_USER')).first()
        if admin_user:
            admin_user.set_password(os.getenv('DJANGO_ADMIN_PASSWORD'))
            admin_user.save()
        else:
            new_admin = User(username=os.getenv('DJANGO_ADMIN_USER'))
            new_admin.set_password(os.getenv('DJANGO_ADMIN_PASSWORD'))
            new_admin.is_superuser = True
            new_admin.is_staff = True
            new_admin.save()

    def handle(self, *args, **options):
        self.create_or_update_admin()
        sys.exit()        
