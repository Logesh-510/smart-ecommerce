import asyncio
import os
import websockets


TOKEN = os.getenv("TEST_WS_TOKEN")


async def test_websocket():
    if not TOKEN:
        raise ValueError("TEST_WS_TOKEN environment variable is not set")

    uri = f"ws://127.0.0.1:8000/ws?token={TOKEN}"

    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket")

        while True:
            message = await websocket.recv()
            print("Received:", message)


asyncio.run(test_websocket())
