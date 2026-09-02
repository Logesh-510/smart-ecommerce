import pytest
import websockets
from websockets.exceptions import InvalidStatus


@pytest.mark.anyio
async def test_websocket_invalid_token():
    fake_token = "this-is-not-a-valid-jwt"

    url = f"ws://127.0.0.1:8000/ws?token={fake_token}"

    with pytest.raises(InvalidStatus):
        async with websockets.connect(url):
            pass