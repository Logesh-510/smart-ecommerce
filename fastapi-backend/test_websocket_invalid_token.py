import asyncio
import websockets


async def test_websocket():

    fake_token = "this-is-not-a-valid-jwt"

    url = f"ws://127.0.0.1:8000/ws?token={fake_token}"

    try:
        async with websockets.connect(url) as websocket:
            print("WebSocket connected with INVALID token!")
            await websocket.wait_closed()

    except Exception as e:
        print("WebSocket connection rejected:")
        print(type(e).__name__, e)


asyncio.run(test_websocket())