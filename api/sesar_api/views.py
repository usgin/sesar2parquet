from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from social_django.utils import psa

from requests.exceptions import HTTPError
from django.core.exceptions import ObjectDoesNotExist


@api_view(['POST'])
@permission_classes([AllowAny])
@psa()
def login_by_access_token(request, backend):
    token = request.data.get('access_token')

    if not token:
        return Response(
                {
                    'errors': {
                        'token': 'Please provide an access token'
                        }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    try:
        user = request.backend.do_auth(token)
    except HTTPError as e:
        status_code = e.response.status_code
        if status_code == 403:
            return Response(
                {
                    'errors': {
                        'token': 'Invalid token'
                        }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            return Response(
                {
                    'error': 'Bad request'
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    if user:
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                'token': token.key
            },
            status=status.HTTP_200_OK,
            )
    else:
        return Response(
                {
                    'errors': {
                        'token': 'Invalid token'
                        }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        

@api_view(['POST'])
def user_details(request):
    return Response(
        {
            'user': str(request.user)
        },
        status=status.HTTP_200_OK,
    )

@api_view(['POST'])
@permission_classes([AllowAny])
def revoke_access_token(request):
    try:
        request.user.auth_token.delete()
    except (AttributeError, ObjectDoesNotExist):
        return Response(
                {
                    'errors': {
                        'token': 'Token does not exist'
                        }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    return Response({"success": ("Successfully logged out.")},
                    status=status.HTTP_200_OK)