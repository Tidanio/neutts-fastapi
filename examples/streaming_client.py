"""Example: HTTP streaming TTS with httpx."""
import httpx

url = "http://localhost:8880/v1/audio/speech"

payload = {
    "model": "neutts-nano-q4-gguf",
    "input": "This is a streaming test. The audio will be sent in chunks as it is generated.",
    "voice": "jo",
    "response_format": "mp3",
    "stream": True,
}

print("Streaming audio...")
with httpx.stream("POST", url, json=payload, timeout=60.0) as response:
    response.raise_for_status()
    with open("output_stream.mp3", "wb") as f:
        for chunk in response.iter_bytes(chunk_size=4096):
            f.write(chunk)
            print(f"  Received {len(chunk)} bytes")

print("Saved: output_stream.mp3")
