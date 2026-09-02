import os

import pytest
import websockets


TOKEN = os.getenv("TEST_WS_TOKEN")


@pytest.mark.anyio
async def test_websocket():
    if not TOKEN:
        pytest.skip("TEST_WS_TOKEN environment variable is not set")

    uri = f"ws://127.0.0.1:8000/ws?token={TOKEN}"

    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket")