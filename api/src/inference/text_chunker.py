from __future__ import annotations

import re


def split_into_sentences(text: str) -> list[str]:
    """Split text into sentences at sentence boundaries."""
    # Split on sentence-ending punctuation followed by whitespace
    parts = re.split(r'(?<=[.!?;])\s+', text.strip())
    return [p.strip() for p in parts if p.strip()]


def chunk_text(text: str, max_chars: int = 500) -> list[str]:
    """Split text into chunks suitable for TTS inference.

    First splits by sentences, then groups sentences into chunks
    that don't exceed max_chars. If a single sentence exceeds
    max_chars, it's split at clause boundaries or word boundaries.
    """
    sentences = split_into_sentences(text)
    if not sentences:
        return [text] if text.strip() else []

    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        if len(sentence) > max_chars:
            # Flush current
            if current:
                chunks.append(current)
                current = ""
            # Split long sentence at clause boundaries
            sub_parts = _split_long_sentence(sentence, max_chars)
            chunks.extend(sub_parts)
        elif len(current) + len(sentence) + 1 > max_chars:
            if current:
                chunks.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip() if current else sentence

    if current:
        chunks.append(current)

    return chunks


def _split_long_sentence(sentence: str, max_chars: int) -> list[str]:
    """Split a long sentence at commas or word boundaries."""
    # Try splitting at commas first
    parts = re.split(r',\s*', sentence)
    if len(parts) > 1:
        result: list[str] = []
        current = ""
        for part in parts:
            candidate = f"{current}, {part}".strip(", ") if current else part
            if len(candidate) > max_chars and current:
                result.append(current)
                current = part
            else:
                current = candidate
        if current:
            result.append(current)
        return result

    # Fallback: split at word boundaries
    words = sentence.split()
    result = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip() if current else word
        if len(candidate) > max_chars and current:
            result.append(current)
            current = word
        else:
            current = candidate
    if current:
        result.append(current)

    return result
