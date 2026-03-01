import json
from asyncio import sleep
from typing import Any, cast

import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.admin.models import LogEntry

from django_admin_shellx.consumers import TerminalConsumer
from django_admin_shellx.models import TerminalCommand

from .asgi import application
from .conftest import BASIC_BASH_COMMANDS, DefaultTimeoutWebsocketCommunicator

pytestmark = pytest.mark.django_db


@database_sync_to_async
def get_history_counts():
    return LogEntry.objects.count(), TerminalCommand.objects.count()


@pytest.mark.asyncio
async def test_websocket_rejects_unauthenticated():
    communicator = DefaultTimeoutWebsocketCommunicator(
        TerminalConsumer.as_asgi(), "/testws/"
    )
    connected, subprotocol = await communicator.connect()
    assert not connected
    assert subprotocol == 4401
    await communicator.disconnect()


@pytest.mark.asyncio
async def test_websocket_rejects_non_superuser_when_required(settings, user_logged_in):
    settings.DJANGO_ADMIN_SHELLX_SUPERUSER_ONLY = True

    communicator = DefaultTimeoutWebsocketCommunicator(
        TerminalConsumer.as_asgi(), "/testws/"
    )
    cast(Any, communicator.scope)["user"] = user_logged_in
    connected, subprotocol = await communicator.connect()
    assert not connected
    assert subprotocol == 4403
    await communicator.disconnect()


@pytest.mark.asyncio
async def test_websocket_rejects_disallowed_origin():
    communicator = WebsocketCommunicator(
        application,
        "/ws/terminal/123/",
        headers=[
            (b"host", b"localhost:8000"),
            (b"origin", b"http://evil.example.com"),
        ],
    )

    connected, _ = await communicator.connect()
    assert not connected

    log_entry_count, terminal_command_count = await get_history_counts()
    assert log_entry_count == 0
    assert terminal_command_count == 0

    await communicator.disconnect()


@pytest.mark.asyncio
async def test_websocket_accepts_authenticated_user(settings, user_logged_in):
    settings.DJANGO_ADMIN_SHELLX_SUPERUSER_ONLY = False

    communicator = DefaultTimeoutWebsocketCommunicator(
        TerminalConsumer.as_asgi(), "/testws/"
    )
    communicator.scope["user"] = user_logged_in
    connected, _ = await communicator.connect()
    assert connected
    # Test sending text
    await communicator.send_to(
        text_data=json.dumps({"action": "input", "data": {"message": "ls"}})
    )
    response = await communicator.receive_from()
    assert response == '{"message": "ls"}'

    await communicator.disconnect()


@pytest.mark.asyncio
async def test_websocket_accepts_authenticated_superuser(superuser_logged_in):
    communicator = DefaultTimeoutWebsocketCommunicator(
        TerminalConsumer.as_asgi(), "/testws/"
    )
    communicator.scope["user"] = superuser_logged_in
    connected, _ = await communicator.connect()
    assert connected
    # Test sending text
    await communicator.send_to(
        text_data=json.dumps({"action": "input", "data": {"message": "ls"}})
    )
    response = await communicator.receive_from()
    assert response == '{"message": "ls"}'

    await communicator.disconnect()


@pytest.mark.asyncio
async def test_websocket_send_command(settings, superuser_logged_in):
    settings.DJANGO_ADMIN_SHELLX_SUPERUSER_ONLY = False
    settings.DJANGO_ADMIN_SHELLX_COMMANDS = BASIC_BASH_COMMANDS
    communicator = DefaultTimeoutWebsocketCommunicator(
        TerminalConsumer.as_asgi(), "/testws/"
    )
    communicator.scope["user"] = superuser_logged_in
    connected, _ = await communicator.connect()
    assert connected

    await communicator.send_to(
        text_data=json.dumps({"action": "input", "data": {"message": "ls\r"}})
    )
    await sleep(3)

    # Responses can go in multiple messages, so we need to wait for all of them
    # Expecting 4 messages from shell
    response = await communicator.receive_from()
    response += await communicator.receive_from()
    # TODO(adinhodovic): This is a hack. We should wait for the response to
    # be complete, which is tricky due to terminal output.
    response += await communicator.receive_from()
    response += await communicator.receive_from()

    assert "LICENSE" in response

    await communicator.disconnect()
