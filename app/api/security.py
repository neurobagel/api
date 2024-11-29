"""Functions for handling authentication. Same ones as used in Neurobagel's federation API."""

import os

import jwt
from fastapi import HTTPException, status
from fastapi.security.utils import get_authorization_scheme_param
from jwt import PyJWKClient, PyJWTError

AUTH_ENABLED = os.environ.get("NB_ENABLE_AUTH", "True").lower() == "true"
CLIENT_ID = os.environ.get("NB_QUERY_CLIENT_ID", None)

KEYS_URL = "https://neurobagel.ca.auth0.com/.well-known/jwks.json"
ISSUER = "https://neurobagel.ca.auth0.com/"

# We only need to define the JWKS client once because get_signing_key_from_jwt will handle key rotations
# by automatically fetching updated keys when needed
# See https://github.com/jpadilla/pyjwt/blob/3ebbb22f30f2b1b41727b269a08b427e9a85d6bb/jwt/jwks_client.py#L96-L115
JWKS_CLIENT = PyJWKClient(KEYS_URL)


def check_client_id():
    """Check if the CLIENT_ID environment variable is set."""
    # The CLIENT_ID is needed to verify the audience claim of ID tokens.
    if AUTH_ENABLED and CLIENT_ID is None:
        raise ValueError(
            "Authentication has been enabled (NB_ENABLE_AUTH) but the environment variable NB_QUERY_CLIENT_ID is not set. "
            "Please set NB_QUERY_CLIENT_ID to the client ID for your Neurobagel query tool deployment, to verify the audience claim of ID tokens."
        )


def verify_token(token: str):
    """Verify the provided ID token. Raise an HTTPException if the token is invalid."""
    try:
        # Extract the token from the "Bearer" scheme
        # (See https://github.com/tiangolo/fastapi/blob/master/fastapi/security/oauth2.py#L473-L485)
        # TODO: Check also if scheme of token is "Bearer"?
        _, extracted_token = get_authorization_scheme_param(token)

        # Determine which key was used to sign the token
        # Adapted from https://pyjwt.readthedocs.io/en/stable/usage.html#retrieve-rsa-signing-keys-from-a-jwks-endpoint
        signing_key = JWKS_CLIENT.get_signing_key_from_jwt(extracted_token)

        id_info = jwt.decode(
            jwt=extracted_token,
            key=signing_key,
            options={
                "verify_signature": True,
                "require": ["aud", "iss", "exp", "iat"],
            },
            audience=CLIENT_ID,
            issuer=ISSUER,
        )
        # TODO: Remove print statement or turn into logging
        print("Token verified: ", id_info)
    except (PyJWTError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
