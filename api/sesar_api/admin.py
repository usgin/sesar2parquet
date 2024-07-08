from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.conf import settings

from sesar_api.models import User, SesarUser


# Define an inline admin descriptor for SesarUser model
# which acts a bit like a singleton
class SesarUserInline(admin.StackedInline):
    model = SesarUser
    can_delete = False


# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = [SesarUserInline]

admin.site.register(User, UserAdmin)