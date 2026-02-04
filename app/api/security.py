"""Functions for handling authentication. Same ones as used in Neurobagel's federation API."""

import jwt
from fastapi import HTTPException, status
from fastapi.security.utils import get_authorization_scheme_param
from jwt import PyJWKClient, PyJWTError

from .env_settings import Settings, settings
from .logger import get_logger, log_and_raise_error

logger = get_logger(__name__)

KEYS_URL = "https://neurobagel.ca.auth0.com/.well-known/jwks.json"
ISSUER = "https://neurobagel.ca.auth0.com/"
# We only need to define the JWKS client once because get_signing_key_from_jwt will handle key rotations
# by automatically fetching updated keys when needed
# See https://github.com/jpadilla/pyjwt/blob/3ebbb22f30f2b1b41727b269a08b427e9a85d6bb/jwt/jwks_client.py#L96-L115
JWKS_CLIENT = PyJWKClient(KEYS_URL)


def check_client_id():
    """Check if the app client ID environment variable is set."""
    # The client ID is needed to verify the audience claim of ID tokens.
    if settings.auth_enabled and settings.client_id is None:
        log_and_raise_error(
            logger,
            RuntimeError,
            f"Authentication has been enabled ({Settings.model_fields['auth_enabled'].alias}) but the environment variable {Settings.model_fields['client_id'].alias} is not set. "
            f"Please set {Settings.model_fields['client_id'].alias} to the client ID for your Neurobagel query tool deployment, to verify the audience claim of ID tokens.",
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

        jwt.decode(
            jwt=extracted_token,
            key=signing_key,
            options={
                "verify_signature": True,
                "require": ["aud", "iss", "exp", "iat"],
            },
            audience=settings.client_id,
            issuer=ISSUER,
        )
    except (PyJWTError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
