from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from django.core.exceptions import ObjectDoesNotExist

TOKEN_LIMIT = 5

@api_view(['POST'])
def get_jwt_for_user(request):
    try:
        if (request.user.sesaruser.upload_permission_status != 1):
            return Response(
                {
                    'errors': {
                        'permissions': 'You do not have permission to generate a jwt.'
                        }
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Count how many outstanding tokens the user already has
        outstanding_tokens = OutstandingToken.objects.filter(user=request.user).order_by('expires_at')

        # If the user exceeds the limit
        if outstanding_tokens.count() >= TOKEN_LIMIT:
            # Revoke the oldest token
            oldest_token = outstanding_tokens.first()
            BlacklistedToken.objects.get_or_create(token=oldest_token)
            oldest_token.delete()  # Remove the outstanding token from the database

        # Now that the limit is respected, issue a new token
        refresh = RefreshToken.for_user(request.user)

        return Response(
            {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            },
            status=status.HTTP_200_OK,
        )
    except (AttributeError, ObjectDoesNotExist):
        return Response(
                {
                    'errors': {
                        'token': 'Token does not exist'
                        }
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )