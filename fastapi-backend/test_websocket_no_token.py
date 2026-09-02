import pytest
import websockets
from websockets.exceptions import InvalidStatus


@pytest.mark.anyio
async def test_websocket_no_token():
    url = "ws://127.0.0.1:8000/ws"

    with pytest.raises(InvalidStatus):
        async with websockets.connect(url):
            pass