import pytest
from channels.testing import WebsocketCommunicator
from django import test
from django.contrib.auth.models import User  # pylint: disable=imported-auth-user

from .factories import UserFactory

BASIC_BASH_COMMANDS = [
    ["env", "-i", "bash", "--norc", "--noprofile"],
]


@pytest.fixture
def user() -> User:
    return UserFactory()


@pytest.fixture
def user_logged_in(client, user, db):  # pylint: disable=redefined-outer-name,unused-argument
    """
    Creates an authenticated user client.
    """
    client.force_login(user)
    return user


@pytest.fixture
def superuser_logged_in(user_logged_in, db):  # pylint: disable=redefined-outer-name,unused-argument
    user_logged_in.is_superuser = True
    user_logged_in.save()
    return user_logged_in


@pytest.fixture
def admin_client(admin_user):
    client = test.Client()
    client.force_login(admin_user)
    client.user = admin_user
    return client


@pytest.fixture
def user_client(user):  # pylint: disable=redefined-outer-name
    client = test.Client()
    client.force_login(user)
    client.user = user
    return client


# Increase the timeout for the WebsocketCommunicator
class DefaultTimeoutWebsocketCommunicator(WebsocketCommunicator):
    """WebsocketCommunicator that provides a configurable default timeout."""

    # Default timeout to use when one is not supplied.
    timeout = 5

    async def connect(self, timeout=None):  # pylint: disable=[signature-differs]
        """
        Trigger the connection code.

        On an accepted connection, returns (True, <chosen-subprotocol>)
        On a rejected connection, returns (False, <close-code>)
        """
        if timeout:
            return await super().connect(timeout=timeout)
        return await super().connect(timeout=self.timeout)

    async def receive_from(self, timeout=None):  # pylint: disable=[signature-differs]
        if timeout:
            return await super().receive_from(timeout=timeout)
        return await super().receive_from(timeout=self.timeout)

    async def receive_json_from(self, timeout=None):  # pylint: disable=[signature-differs]
        if timeout:
            return await super().receive_json_from(timeout=timeout)
        return await super().receive_json_from(timeout=self.timeout)

    async def disconnect(self, code=1000, timeout=None):  # pylint: disable=[signature-differs]
        if timeout:
            return await super().disconnect(code=code, timeout=timeout)
        return await super().disconnect(code=code, timeout=self.timeout)
