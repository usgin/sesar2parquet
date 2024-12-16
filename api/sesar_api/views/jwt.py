from django.contrib.auth import authenticate
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.views import TokenRefreshView
from sesar_api.classes.CustomRefreshToken import CustomRefreshToken
from django.contrib.auth import get_user_model

from django.core.exceptions import ObjectDoesNotExist

TOKEN_LIMIT = 5

@api_view(['GET'])
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
        outstanding_tokens = OutstandingToken.objects.filter(
            user=request.user
        ).exclude(
            id__in=BlacklistedToken.objects.values_list('token_id', flat=True)
        ).order_by('expires_at')

        tokens_without_connection = []
        for token in outstanding_tokens:
            try:
                payload = RefreshToken(token.token).payload
                if 'connection' not in payload:
                    tokens_without_connection.append(token)
            except (TokenError, InvalidToken):
                # Delete tokens that are invalid or expired
                token.delete()
        # If the user exceeds the limit
        if len(tokens_without_connection) >= TOKEN_LIMIT:
            # Revoke the oldest token
            oldest_token = tokens_without_connection[0]
            BlacklistedToken.objects.get_or_create(token=oldest_token)

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


# create jwt with custom connection claim
@api_view(['POST'])
@permission_classes([AllowAny])
def get_jwt_for_user_with_connection(request, connection):
    try:
        user = None
        # Check for TokenAuthentication
        try:
            token_auth = TokenAuthentication()
            result = token_auth.authenticate(request)
            if result is not None:
                user, token = result
        except AuthenticationFailed:
            pass

        # Check for ORCID ID Token using custom authentication backend
        if user is None:
            token = request.POST.get("token")
            user = authenticate(request, token=token)

        if user is None:
            return Response(
                {
                    'error': 'The given ORCID JWT is either invalid or no associated user was found.'
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if (user.sesaruser.upload_permission_status != 1):
            return Response(
                {
                    'errors': {
                        'permissions': 'You do not have permission to generate a jwt.'
                        }
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Count how many outstanding tokens the user already has
        outstanding_tokens = OutstandingToken.objects.filter(
            user=user
        ).exclude(
            id__in=BlacklistedToken.objects.values_list('token_id', flat=True)
        ).order_by('expires_at')

        # only one jwt allowed per connection, blacklist the existing one
        for token in outstanding_tokens:
            try:
                # Decode the token payload
                payload = RefreshToken(token.token).payload
                if payload.get('connection') == connection:
                    BlacklistedToken.objects.get_or_create(token=token)
            except (TokenError, InvalidToken):
                # Delete tokens that are invalid or expired
                token.delete()

        # Now that the limit is respected, issue a new token
        refresh = CustomRefreshToken.for_user_with_connection(user, connection)
        access = refresh.access_token
        access['connection'] = connection

        return Response(
            {
                'refresh': str(refresh),
                'access': str(access) 
            },
            status=status.HTTP_201_CREATED,
        )
    except (ObjectDoesNotExist):
        return Response(
                {
                    'error': 'An unknown error has occurred.'
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )


class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"error": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Decode the existing refresh token
            original_token = RefreshToken(refresh_token)

            # Retrieve custom claims from the original token
            connection = original_token.get("connection", None)
            AuthUser = get_user_model()
            user = AuthUser.objects.get(id = original_token.payload.get('user_id'))

            # Blacklist the old refresh token
            try:
                blacklist_token = OutstandingToken.objects.get(token=str(original_token))
                BlacklistedToken.objects.get_or_create(token=blacklist_token)
            except Exception as e:
                return Response(
                    {"error": e},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            
            if connection:
                new_refresh_token = CustomRefreshToken.for_user_with_connection(user, connection)
            else:
                new_refresh_token = RefreshToken.for_user(user)

            # Generate a new access token
            new_access_token = new_refresh_token.access_token

            if connection:
                new_access_token["connection"] = connection  # Add custom claim to access token

            return Response(
                {
                    "refresh": str(new_refresh_token),
                    "access": str(new_access_token),
                },
                status=status.HTTP_200_OK,
            )

        except (TokenError, InvalidToken):
            return Response(
                {"error": "Invalid or expired refresh token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )


@api_view(['GET'])
def revoke_all_jwt_for_user(request):
    # Get all outstanding tokens for the user
    outstanding_tokens = OutstandingToken.objects.filter(
        user=request.user
    ).exclude(
        id__in=BlacklistedToken.objects.values_list('token_id', flat=True)
    ).order_by('expires_at')
    count = 0

    tokens_without_connection = []
    for token in outstanding_tokens:
        try:
            payload = RefreshToken(token.token).payload
            if 'connection' not in payload:
                tokens_without_connection.append(token)
        except (TokenError, InvalidToken):
            # Delete tokens that are invalid or expired
            token.delete()
    # Loop through the outstanding tokens and blacklist each one
    for token in tokens_without_connection:
        # Blacklist the token if it's not already blacklisted
        _, created = BlacklistedToken.objects.get_or_create(token=token)
        
        if created:
            count += 1

    return Response(
        {
        'message': f"All {count} token(s) have been revoked.",
        },
        status=status.HTTP_200_OK,
    )