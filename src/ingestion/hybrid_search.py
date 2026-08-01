from __future__ import annotations

import argparse
import json
import os
import re
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from fastembed import SparseTextEmbedding
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer


# ============================================================
# Paths and model configuration
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_PROCESSED_ROOT = (
    PROJECT_ROOT / "data" / "processed"
)

DEFAULT_QDRANT_PATH = (
    PROJECT_ROOT / "data" / "indexes" / "qdrant"
)

DEFAULT_INDEX_MANIFEST = (
    PROJECT_ROOT
    / "data"
    / "indexes"
    / "hybrid-index-report.json"
)

DEFAULT_COLLECTION_NAME = "security-book-chunks-v1"

DENSE_MODEL_NAME = "google/embeddinggemma-300m"
SPARSE_MODEL_NAME = "Qdrant/bm25"

DENSE_VECTOR_NAME = "dense"
SPARSE_VECTOR_NAME = "sparse"

TOKEN_PATTERN = re.compile(r"\w+|[^\w\s]")


# ============================================================
# Basic file helpers
# ============================================================

def resolve_project_path(path: Path) -> Path:
    if path.is_absolute():
        return path.resolve()

    return (PROJECT_ROOT / path).resolve()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        value = json.load(file)

    if not isinstance(value, dict):
        raise ValueError(
            f"Expected a JSON object in {path}"
        )

    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON in {path}, "
                    f"line {line_number}: {error}"
                ) from error

            if not isinstance(record, dict):
                raise ValueError(
                    f"Expected a JSON object in {path}, "
                    f"line {line_number}"
                )

            records.append(record)

    return records


def write_json_atomic(
    path: Path,
    value: dict[str, Any],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = path.with_name(
        path.name + ".tmp"
    )

    with temporary_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            value,
            file,
            ensure_ascii=False,
            indent=2,
        )
        file.write("\n")

    temporary_path.replace(path)




# ============================================================
# Corpus loading and validation
# ============================================================

def load_corpus(
    processed_root: Path,
    selected_document_ids: set[str] | None = None,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    if not processed_root.exists():
        raise FileNotFoundError(
            f"Processed data directory not found: "
            f"{processed_root}"
        )

    chunks: list[dict[str, Any]] = []
    parents: list[dict[str, Any]] = []
    discovered_document_ids: set[str] = set()

    for document_directory in sorted(
        processed_root.iterdir()
    ):
        if not document_directory.is_dir():
            continue

        document_id = document_directory.name

        if (
            selected_document_ids
            and document_id not in selected_document_ids
        ):
            continue

        chunks_path = (
            document_directory / "chunks.jsonl"
        )
        parents_path = (
            document_directory / "parents.jsonl"
        )

        if not chunks_path.exists():
            continue

        if not parents_path.exists():
            raise FileNotFoundError(
                f"Missing parent file: {parents_path}"
            )

        document_chunks = load_jsonl(chunks_path)
        document_parents = load_jsonl(parents_path)

        chunks.extend(document_chunks)
        parents.extend(document_parents)
        discovered_document_ids.add(document_id)

    if selected_document_ids:
        missing_document_ids = (
            selected_document_ids
            - discovered_document_ids
        )

        if missing_document_ids:
            raise ValueError(
                "Processed data was not found for: "
                + ", ".join(
                    sorted(missing_document_ids)
                )
            )

    if not chunks:
        raise ValueError(
            f"No chunks were found under {processed_root}"
        )

    validate_corpus(chunks, parents)

    chunks.sort(
        key=lambda chunk: str(chunk["chunk_id"])
    )

    parents.sort(
        key=lambda parent: str(parent["parent_id"])
    )

    return chunks, parents

