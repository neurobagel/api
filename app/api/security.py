"""Functions for handling authentication. Same ones as used in Neurobagel's federation API."""

import os

from fastapi import HTTPException, status
from fastapi.security.utils import get_authorization_scheme_param
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests
from google.oauth2 import id_token

AUTH_ENABLED = os.environ.get("NB_ENABLE_AUTH", "True").lower() == "true"
CLIENT_ID = os.environ.get("NB_QUERY_CLIENT_ID", None)


def check_client_id():
    """Check if the CLIENT_ID environment variable is set."""
    # By default, if CLIENT_ID is not provided to verify_oauth2_token,
    # Google will simply skip verifying the audience claim of ID tokens.
    # This however can be a security risk, so we mandate that CLIENT_ID is set.
    if AUTH_ENABLED and CLIENT_ID is None:
        raise ValueError(
            "Authentication has been enabled (NB_ENABLE_AUTH) but the environment variable NB_QUERY_CLIENT_ID is not set. "
            "Please set NB_QUERY_CLIENT_ID to the Google client ID for your Neurobagel query tool deployment, to verify the audience claim of ID tokens."
        )


def verify_token(token: str):
    """Verify the Google ID token. Raise an HTTPException if the token is invalid."""
    # Adapted from https://developers.google.com/identity/gsi/web/guides/verify-google-id-token#python
    try:
        # Extract the token from the "Bearer" scheme
        # (See https://github.com/tiangolo/fastapi/blob/master/fastapi/security/oauth2.py#L473-L485)
        # TODO: Check also if scheme of token is "Bearer"?
        _, param = get_authorization_scheme_param(token)
        id_info = id_token.verify_oauth2_token(
            param, requests.Request(), CLIENT_ID
        )
        # TODO: Remove print statement or turn into logging
        print("Token verified: ", id_info)
    except (GoogleAuthError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
