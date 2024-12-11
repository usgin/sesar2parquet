from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from datetime import datetime, timezone

class CustomRefreshToken(RefreshToken):
    @classmethod
    def for_user_with_connection(cls, user, connection):
        token = cls.for_user(user)
        token['connection'] = connection

        jti = token['jti']

        # correct outstanding token record with updated claim
        try:
            outstanding_token = OutstandingToken.objects.get(jti=jti)
            outstanding_token.token = str(token)
            outstanding_token.save()
        except OutstandingToken.DoesNotExist:
            pass

        return token