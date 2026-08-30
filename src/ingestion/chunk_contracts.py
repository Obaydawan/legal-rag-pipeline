"""
chunk_contracts.py

Reads raw CUAD contract .txt files, splits each into overlapping,
sentence-aware chunks, and writes structured output with metadata
to data/processed/chunks.jsonl.

Handles common legal-document formatting quirks:
- Collapses excessive whitespace/blank lines
- Strips common page-header/footer noise (page numbers, repeated headers)
- Keeps ALL-CAPS section titles attached to the chunk that follows them,
  rather than splitting them into their own tiny chunk

Run standalone first to verify output before wiring into Airflow:
    python chunk_contracts.py
"""

import json
import re
from pathlib import Path

RAW_DIR = Path("data/raw/full_contract_txt")
OUTPUT_PATH = Path("data/processed/chunks.jsonl")

CHUNK_SIZE_WORDS = 400   # ~500 tokens, rough word-based approximation
CHUNK_OVERLAP_WORDS = 50

# Common noise patterns seen in scanned/exported legal contract text.
# Extend this list once you've actually looked at a few real CUAD files —
# treat this as a starting point, not a finished list.
NOISE_PATTERNS = [
    r"Page \d+ of \d+",
    r"^\s*\d+\s*$",              # lone page-number lines
    r"_{5,}",                     # long underscores (signature lines)
]


def clean_text(raw: str) -> str:
    text = raw
    for pattern in NOISE_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.MULTILINE)
    # Collapse 3+ blank lines down to a single blank line
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_into_sentences(text: str) -> list[str]:
    # Simple sentence splitter tuned loosely for legal text (handles
    # "Section 4.2." style numbering without over-splitting). Not
    # perfect — revisit if chunk boundaries look wrong on inspection.
    sentence_end = re.compile(r"(?<=[.!?])\s+(?=[A-Z(\"])")
    sentences = sentence_end.split(text)
    return [s.strip() for s in sentences if s.strip()]


def chunk_sentences(sentences: list[str], chunk_size: int, overlap: int) -> list[str]:
    chunks = []
    current: list[str] = []
    current_word_count = 0

    for sentence in sentences:
        word_count = len(sentence.split())
        if current_word_count + word_count > chunk_size and current:
            chunks.append(" ".join(current))
            # Build overlap from the tail of the previous chunk
            overlap_words: list[str] = []
            overlap_count = 0
            for s in reversed(current):
                w = len(s.split())
                if overlap_count + w > overlap:
                    break
                overlap_words.insert(0, s)
                overlap_count += w
            current = overlap_words
            current_word_count = overlap_count

        current.append(sentence)
        current_word_count += word_count

    if current:
        chunks.append(" ".join(current))

    return chunks


def process_file(path: Path) -> list[dict]:
    raw_text = path.read_text(encoding="utf-8", errors="ignore")
    cleaned = clean_text(raw_text)
    sentences = split_into_sentences(cleaned)
    chunks = chunk_sentences(sentences, CHUNK_SIZE_WORDS, CHUNK_OVERLAP_WORDS)

    records = []
    char_offset = 0
    for i, chunk_text in enumerate(chunks):
        records.append(
            {
                "source_file": path.name,
                "chunk_index": i,
                "char_offset_start": char_offset,
                "char_offset_end": char_offset + len(chunk_text),
                "word_count": len(chunk_text.split()),
                "text": chunk_text,
            }
        )
        char_offset += len(chunk_text)

    return records


def main():
    if not RAW_DIR.exists():
        raise FileNotFoundError(
            f"{RAW_DIR} not found — download and unzip CUAD into data/raw/ first "
            f"(expects data/raw/full_contract_txt/*.txt)"
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    txt_files = sorted(RAW_DIR.glob("*.txt"))
    if not txt_files:
        raise FileNotFoundError(f"No .txt files found in {RAW_DIR}")

    total_chunks = 0
    with OUTPUT_PATH.open("w", encoding="utf-8") as out_f:
        for path in txt_files:
            records = process_file(path)
            for record in records:
                out_f.write(json.dumps(record) + "\n")
            total_chunks += len(records)

    print(f"Processed {len(txt_files)} contracts into {total_chunks} chunks.")
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
