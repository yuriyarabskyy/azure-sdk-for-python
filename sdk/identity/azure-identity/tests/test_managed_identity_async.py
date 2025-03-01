# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------
import time
from unittest import mock

from azure.core.credentials import AccessToken
from azure.identity.aio import ManagedIdentityCredential
from azure.identity.constants import Endpoints, EnvironmentVariables
import pytest

from helpers import async_validating_transport, mock_response, Request


@pytest.mark.asyncio
async def test_cloud_shell():
    """Cloud Shell environment: only MSI_ENDPOINT set"""

    access_token = "****"
    expires_on = 42
    expected_token = AccessToken(access_token, expires_on)
    url = "http://localhost:42/token"
    scope = "scope"
    transport = async_validating_transport(
        requests=[
            Request(url, method="POST", required_headers={"Metadata": "true"}, required_data={"resource": scope})
        ],
        responses=[
            mock_response(
                json_payload={
                    "access_token": access_token,
                    "expires_in": 0,
                    "expires_on": expires_on,
                    "not_before": int(time.time()),
                    "resource": scope,
                    "token_type": "Bearer",
                }
            )
        ],
    )

    with mock.patch("os.environ", {EnvironmentVariables.MSI_ENDPOINT: url}):
        token = await ManagedIdentityCredential(transport=transport).get_token(scope)
        assert token == expected_token


@pytest.mark.asyncio
async def test_cloud_shell_user_assigned_identity():
    """Cloud Shell environment: only MSI_ENDPOINT set"""

    access_token = "****"
    expires_on = 42
    client_id = "some-guid"
    expected_token = AccessToken(access_token, expires_on)
    url = "http://localhost:42/token"
    scope = "scope"
    transport = async_validating_transport(
        requests=[
            Request(
                url,
                method="POST",
                required_headers={"Metadata": "true"},
                required_data={"client_id": client_id, "resource": scope},
            )
        ],
        responses=[
            mock_response(
                json_payload={
                    "access_token": access_token,
                    "expires_in": 0,
                    "expires_on": expires_on,
                    "not_before": int(time.time()),
                    "resource": scope,
                    "token_type": "Bearer",
                }
            )
        ],
    )

    with mock.patch("os.environ", {EnvironmentVariables.MSI_ENDPOINT: url}):
        token = await ManagedIdentityCredential(client_id=client_id, transport=transport).get_token(scope)
        assert token == expected_token


@pytest.mark.asyncio
async def test_app_service():
    """App Service environment: MSI_ENDPOINT, MSI_SECRET set"""

    access_token = "****"
    expires_on = 42
    expected_token = AccessToken(access_token, expires_on)
    url = "http://localhost:42/token"
    secret = "expected-secret"
    scope = "scope"
    transport = async_validating_transport(
        requests=[
            Request(
                url,
                method="GET",
                required_headers={"Metadata": "true", "secret": secret},
                required_params={"api-version": "2017-09-01", "resource": scope},
            )
        ],
        responses=[
            mock_response(
                json_payload={
                    "access_token": access_token,
                    "expires_on": expires_on,
                    "resource": scope,
                    "token_type": "Bearer",
                }
            )
        ],
    )

    with mock.patch("os.environ", {EnvironmentVariables.MSI_ENDPOINT: url, EnvironmentVariables.MSI_SECRET: secret}):
        token = await ManagedIdentityCredential(transport=transport).get_token(scope)
        assert token == expected_token


@pytest.mark.asyncio
async def test_app_service_user_assigned_identity():
    """App Service environment: MSI_ENDPOINT, MSI_SECRET set"""

    access_token = "****"
    expires_on = 42
    client_id = "some-guid"
    expected_token = AccessToken(access_token, expires_on)
    url = "http://localhost:42/token"
    secret = "expected-secret"
    scope = "scope"
    transport = async_validating_transport(
        requests=[
            Request(
                url,
                method="GET",
                required_headers={"Metadata": "true", "secret": secret},
                required_params={"api-version": "2017-09-01", "client_id": client_id, "resource": scope},
            )
        ],
        responses=[
            mock_response(
                json_payload={
                    "access_token": access_token,
                    "expires_on": expires_on,
                    "resource": scope,
                    "token_type": "Bearer",
                }
            )
        ],
    )

    with mock.patch("os.environ", {EnvironmentVariables.MSI_ENDPOINT: url, EnvironmentVariables.MSI_SECRET: secret}):
        token = await ManagedIdentityCredential(client_id=client_id, transport=transport).get_token(scope)
        assert token == expected_token


@pytest.mark.asyncio
async def test_imds():
    access_token = "****"
    expires_on = 42
    expected_token = AccessToken(access_token, expires_on)
    url = Endpoints.IMDS
    scope = "scope"
    transport = async_validating_transport(
        requests=[
            Request(url),  # first request should be availability probe => match only the URL
            Request(
                url,
                method="GET",
                required_headers={"Metadata": "true"},
                required_params={"api-version": "2018-02-01", "resource": scope},
            ),
        ],
        responses=[
            # probe receives error response
            mock_response(status_code=400, json_payload={"error": "this is an error message"}),
            mock_response(
                json_payload={
                    "access_token": access_token,
                    "expires_in": 42,
                    "expires_on": expires_on,
                    "ext_expires_in": 42,
                    "not_before": int(time.time()),
                    "resource": scope,
                    "token_type": "Bearer",
                }
            ),
        ],
    )

    token = await ManagedIdentityCredential(transport=transport).get_token(scope)
    assert token == expected_token


@pytest.mark.asyncio
async def test_imds_user_assigned_identity():
    access_token = "****"
    expires_on = 42
    expected_token = AccessToken(access_token, expires_on)
    url = Endpoints.IMDS
    scope = "scope"
    client_id = "some-guid"
    transport = async_validating_transport(
        requests=[
            Request(url),  # first request should be availability probe => match only the URL
            Request(
                url,
                method="GET",
                required_headers={"Metadata": "true"},
                required_params={"api-version": "2018-02-01", "client_id": client_id, "resource": scope},
            ),
        ],
        responses=[
            # probe receives error response
            mock_response(status_code=400, json_payload={"error": "this is an error message"}),
            mock_response(
                json_payload={
                    "access_token": access_token,
                    "client_id": client_id,
                    "expires_in": 42,
                    "expires_on": expires_on,
                    "ext_expires_in": 42,
                    "not_before": int(time.time()),
                    "resource": scope,
                    "token_type": "Bearer",
                }
            ),
        ],
    )

    token = await ManagedIdentityCredential(client_id=client_id, transport=transport).get_token(scope)
    assert token == expected_token
