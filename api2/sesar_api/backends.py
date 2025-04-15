import jwt
import requests
from django.contrib.auth.backends import BaseBackend
from sesar_api.models import SesarUser

class ORCIDAuthenticationBackend(BaseBackend):
    def authenticate(self, request, token=None):
        """
        Authenticate a user based on an ORCID JWT.
        """
        if not token:
            return None
        
        # Decode and verify the JWT
        try:
            # Fetch ORCID's public keys
            response = requests.get("https://orcid.org/.well-known/openid-configuration")
            response.raise_for_status()
            jwks_uri = response.json()['jwks_uri']

            jwks_response = requests.get(jwks_uri)
            jwks_response.raise_for_status()
            jwks = jwks_response.json()

            # Get the key matching the JWT header
            unverified_header = jwt.get_unverified_header(token)
            public_keys = {key["kid"]: key for key in jwks["keys"]}
            key = public_keys.get(unverified_header["kid"])

            if not key:
                raise ValueError("Public key for the JWT not found.")

            # Verify the token
            orcid_data = jwt.decode(
                token,
                jwt.algorithms.RSAAlgorithm.from_jwk(key),
                algorithms=["RS256"],
                issuer="https://orcid.org",
                options={"verify_aud": False}
            )
        except (jwt.ExpiredSignatureError, jwt.DecodeError, ValueError, requests.RequestException) as e:
            print(f"JWT verification failed: {e}")
            return None

        # Extract ORCID iD from the payload
        orcid_id = orcid_data.get("sub")
        if not orcid_id:
            return None

        try:
            user = SesarUser.objects.get(orcid=orcid_id).auth_user
            return user
        except SesarUser.DoesNotExist:
            return None