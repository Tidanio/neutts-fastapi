"""Example: WebSocket real-time TTS streaming."""
import asyncio
import base64
import json

import websockets


async def main():
    uri = "ws://localhost:8880/v1/audio/speech/stream"

    async with websockets.connect(uri) as ws:
        # 1. Start session
        await ws.send(json.dumps({
            "type": "start",
            "model": "neutts-nano-q4-gguf",
            "voice": "jo",
            "response_format": "pcm",
        }))

        # 2. Send text
        await ws.send(json.dumps({
            "type": "text",
            "text": "Hello! This is a real-time streaming test via WebSocket.",
        }))

        # 3. Receive audio chunks
        audio_data = b""
        while True:
            raw = await ws.recv()
            msg = json.loads(raw)

            if msg["type"] == "audio":
                chunk = base64.b64decode(msg["data"])
                audio_data += chunk
                print(f"  Received audio chunk: {len(chunk)} bytes")

            elif msg["type"] == "done":
                print("Stream complete!")
                break

            elif msg["type"] == "error":
                print(f"Error: {msg['message']}")
                break

        # 4. Stop session
        await ws.send(json.dumps({"type": "stop"}))

        # Save raw PCM (24kHz, 16-bit, mono)
        with open("output_ws.pcm", "wb") as f:
            f.write(audio_data)
        print(f"Saved: output_ws.pcm ({len(audio_data)} bytes)")
        print("Play with: ffplay -f s16le -ar 24000 -ac 1 output_ws.pcm")


if __name__ == "__main__":
    asyncio.run(main())
