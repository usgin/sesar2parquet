from .models import SesarUser
from django.core.exceptions import ObjectDoesNotExist

from django.forms.models import model_to_dict

def save_sesar_user(backend, user, response, *args, **kwargs):
    if backend.name == 'oidc':
        # if no associated sesar user
        if not hasattr(user, "sesaruser"):
            # check if there is an existing sesar user that needs to be linked
            try:
                sesar_user = SesarUser.objects.get(orcid=response['sub'])
                sesar_user.auth_user = user
                sesar_user.save()
            # if sesar user does not exist, create one
            except SesarUser.DoesNotExist:
                new_sesar_user = SesarUser(auth_user=user)
                new_sesar_user.fname = response['given_name']
                new_sesar_user.lname = response['family_name']
                new_sesar_user.orcid = response['sub']
                new_sesar_user.save()