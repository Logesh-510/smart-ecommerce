import asyncio
import websockets


TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5Iiwicm9sZSI6ImN1c3RvbWVyIiwidHlwZSI6ImFjY2VzcyIsImV4cCI6MTc4NzY0MjQxOH0.8N-62NQOXtj8LIel-lPGI5PdSIQ2NONCezmHMf_Qtno"


async def test_websocket():

    url = f"ws://127.0.0.1:8000/ws?token={TOKEN}"

    try:
        async with websockets.connect(url) as websocket:

            print("WebSocket connected successfully!")
            print("Waiting for real-time notifications...")

            while True:
                message = await websocket.recv()

                print("Received:", message)

    except Exception as e:
        print("WebSocket connection failed:", e)


asyncio.run(test_websocket())