from __future__ import annotations

import pytest

from api.src.core.model_config import BUILTIN_VOICES, BACKBONE_MODELS, CODEC_MODELS
from api.src.inference.text_chunker import chunk_text, split_into_sentences


class TestModelConfig:
    def test_backbone_models_count(self):
        assert len(BACKBONE_MODELS) == 16

    def test_codec_models_count(self):
        assert len(CODEC_MODELS) == 4

    def test_builtin_voices_count(self):
        assert len(BUILTIN_VOICES) == 8

    def test_all_backbone_models_have_repo(self):
        for model_id, info in BACKBONE_MODELS.items():
            assert info.repo.startswith("neuphonic/"), f"{model_id} has invalid repo"
            assert info.language in ("en-us", "de", "fr-fr", "es")

    def test_streaming_only_gguf(self):
        for model_id, info in BACKBONE_MODELS.items():
            if info.supports_streaming:
                assert "gguf" in model_id, f"{model_id} supports streaming but is not GGUF"

    def test_builtin_voice_languages(self):
        languages = {v["language"] for v in BUILTIN_VOICES.values()}
        assert "en-us" in languages
        assert "de" in languages
        assert "fr-fr" in languages
        assert "es" in languages


class TestTextChunker:
    def test_short_text(self):
        chunks = chunk_text("Hello world.")
        assert len(chunks) == 1
        assert chunks[0] == "Hello world."

    def test_multiple_sentences(self):
        text = "First sentence. Second sentence. Third sentence."
        chunks = chunk_text(text, max_chars=30)
        assert len(chunks) >= 2

    def test_empty_text(self):
        assert chunk_text("") == []
        assert chunk_text("   ") == []

    def test_split_into_sentences(self):
        text = "Hello! How are you? I am fine. Thanks."
        sentences = split_into_sentences(text)
        assert len(sentences) == 4

    def test_long_sentence_splitting(self):
        long_text = "This is a very long sentence " * 50
        chunks = chunk_text(long_text.strip(), max_chars=200)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= 250  # Allow some tolerance

    def test_preserves_content(self):
        text = "Hello world. This is a test. Have a nice day."
        chunks = chunk_text(text, max_chars=500)
        reassembled = " ".join(chunks)
        assert reassembled == text


class TestVoiceEndpoints:
    def test_delete_builtin_voice_fails(self, client):
        resp = client.delete("/v1/audio/voices/dave")
        assert resp.status_code == 400

    def test_delete_nonexistent_voice(self, client):
        resp = client.delete("/v1/audio/voices/nonexistent")
        assert resp.status_code == 400
