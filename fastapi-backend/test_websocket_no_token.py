import asyncio
import websockets


async def test_websocket():

    url = "ws://127.0.0.1:8000/ws"

    try:
        async with websockets.connect(url) as websocket:
            print("WebSocket connected WITHOUT token!")
            await websocket.wait_closed()

    except Exception as e:
        print("WebSocket connection rejected:")
        print(type(e).__name__, e)


asyncio.run(test_websocket())