from __future__ import annotations

import pytest

from api.src.structures.schemas import OpenAISpeechRequest, VoiceListResponse, ModelListResponse


class TestSchemas:
    def test_speech_request_defaults(self):
        req = OpenAISpeechRequest(input="Hello world")
        assert req.model == "neutts-nano-q4-gguf"
        assert req.voice == "jo"
        assert req.response_format == "mp3"
        assert req.speed == 1.0
        assert req.stream is False

    def test_speech_request_custom(self):
        req = OpenAISpeechRequest(
            model="neutts-nano-german-q4-gguf",
            input="Hallo Welt",
            voice="greta",
            response_format="wav",
            speed=1.5,
            stream=True,
        )
        assert req.model == "neutts-nano-german-q4-gguf"
        assert req.voice == "greta"
        assert req.response_format == "wav"
        assert req.speed == 1.5
        assert req.stream is True

    def test_speech_request_input_required(self):
        with pytest.raises(Exception):
            OpenAISpeechRequest()

    def test_speech_request_speed_bounds(self):
        with pytest.raises(Exception):
            OpenAISpeechRequest(input="test", speed=0.1)
        with pytest.raises(Exception):
            OpenAISpeechRequest(input="test", speed=5.0)

    def test_speech_request_format_validation(self):
        for fmt in ("mp3", "opus", "aac", "flac", "wav", "pcm"):
            req = OpenAISpeechRequest(input="test", response_format=fmt)
            assert req.response_format == fmt

    def test_voice_list_response(self):
        resp = VoiceListResponse(voices=[])
        assert resp.voices == []

    def test_model_list_response(self):
        resp = ModelListResponse(data=[])
        assert resp.object == "list"
        assert resp.data == []


class TestHealthEndpoint:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestModelEndpoints:
    def test_list_models(self, client):
        resp = client.get("/v1/models")
        assert resp.status_code == 200
        data = resp.json()
        assert data["object"] == "list"
        assert isinstance(data["data"], list)

    def test_get_unknown_model(self, client):
        resp = client.get("/v1/models/nonexistent")
        assert resp.status_code == 404

    def test_model_registry(self, client):
        resp = client.get("/v1/models/registry")
        assert resp.status_code == 200
        data = resp.json()
        assert "backbones" in data
        assert "codecs" in data
        assert len(data["backbones"]) == 16
        assert len(data["codecs"]) == 4


class TestVoiceEndpoints:
    def test_list_voices(self, client):
        resp = client.get("/v1/audio/voices")
        assert resp.status_code == 200
        data = resp.json()
        assert "voices" in data
        names = {v["name"] for v in data["voices"]}
        assert "dave" in names
        assert "jo" in names
        assert "greta" in names


class TestSpeechEndpoint:
    def test_speech_no_model_loaded(self, client):
        resp = client.post("/v1/audio/speech", json={
            "model": "neutts-nano-q4-gguf",
            "input": "Hello",
            "voice": "jo",
        })
        # Should fail because no model is loaded in test
        assert resp.status_code in (400, 500)
