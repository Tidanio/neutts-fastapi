"""Example: Using NeuTTS-FastAPI with the official OpenAI Python SDK."""
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8880/v1",
    api_key="not-needed",
)

# English TTS
response = client.audio.speech.create(
    model="neutts-nano-q4-gguf",
    voice="jo",
    input="Hello! This is a test of the NeuTTS text-to-speech system.",
)
response.stream_to_file("output_en.mp3")
print("Saved: output_en.mp3")

# German TTS
response = client.audio.speech.create(
    model="neutts-nano-german-q4-gguf",
    voice="greta",
    input="Hallo Welt! Dies ist ein Test des NeuTTS Text-zu-Sprache Systems.",
)
response.stream_to_file("output_de.mp3")
print("Saved: output_de.mp3")

# French TTS
response = client.audio.speech.create(
    model="neutts-nano-french-q4-gguf",
    voice="juliette",
    input="Bonjour le monde! Ceci est un test du systeme NeuTTS.",
)
response.stream_to_file("output_fr.mp3")
print("Saved: output_fr.mp3")

# Spanish TTS
response = client.audio.speech.create(
    model="neutts-nano-spanish-q4-gguf",
    voice="mateo",
    input="Hola mundo! Esta es una prueba del sistema NeuTTS.",
)
response.stream_to_file("output_es.mp3")
print("Saved: output_es.mp3")
