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




def validate_corpus(
        chunks: list[dict[str, Any]],
        parents: list[dict[str, Any]],
    ) -> None:
        chunk_ids: set[str] = set()
        parent_ids: set[str] = set()

        for parent in parents:
            parent_id = str(
                parent.get("parent_id", "")
            ).strip()

            if not parent_id:
                raise ValueError(
                    "A parent record has no parent_id"
                )

            if parent_id in parent_ids:
                raise ValueError(
                    f"Duplicate parent_id: {parent_id}"
                )

            parent_ids.add(parent_id)

        for chunk in chunks:
            chunk_id = str(
                chunk.get("chunk_id", "")
            ).strip()

            parent_id = str(
                chunk.get("parent_id", "")
            ).strip()

            text = str(
                chunk.get("text", "")
            ).strip()

            if not chunk_id:
                raise ValueError(
                    "A chunk record has no chunk_id"
                )

            if chunk_id in chunk_ids:
                raise ValueError(
                    f"Duplicate chunk_id: {chunk_id}"
                )

            if not parent_id:
                raise ValueError(
                    f"Chunk {chunk_id} has no parent_id"
                )

            if parent_id not in parent_ids:
                raise ValueError(
                    f"Chunk {chunk_id} references missing "
                    f"parent {parent_id}"
                )

            if not text:
                raise ValueError(
                    f"Chunk {chunk_id} has empty text"
                )

            chunk_ids.add(chunk_id)

# ============================================================
# Text preparation
# ============================================================

def approximate_token_count(text: str) -> int:
    return len(TOKEN_PATTERN.findall(text))



def create_dense_text(
        chunk: dict[str , Any]
) -> str:

    """
    chunk = {
    "title": "Python Basics",
    "heading_path": ["Chapter 1", "Introduction", "Variables"],
    "text": "Variables store data values.",
}

print(create_dense_text(chunk))


Title : Python Basics
Section: {heading_path}

Variables store data values.
    
    
    """

    embedding_text = str(
        chunk.get("embedding_text" , "")
    ).strip()

    if embedding_text:
        return embedding_text

    title = str(
        chunk.get("title" , "")
    ).strip()

    heading_path_value = chunk.get(
        "heading_path" , 
        [],
    )

    if isinstance(heading_path_value , list):
        heading_path = " > ".join(
            str(value).strip() 
            for value in heading_path_value
            if str(value).strip()
        ) 
    else:
        heading_path = str(
            heading_path_value
        ).strip()


    text = str(chunk["text"]).strip()

    values = []

    if title:
        values.append(f"Title : {title}")

    if heading_path:
        values.append("Section: {heading_path}"
        )

    values.extend(["", text])
    
    return "\n".join(values).strip()

def create_lexical_text(
    chunk: dict[str, Any],
) -> str:
    """
    Text used for BM25.

    Repeating important metadata here gives exact title and
    heading terms a chance to match the query.


    chunk = {
    "title": "Python Basics",
    "heading_path": ["Chapter 1", "Introduction", "Variables"],
    "text": "Variables store data values.",
}

print(create_lexical_text(chunk))


["Python Basics", "Chapter 1 Introduction Variables", "Variables store data values."]
    """
    values: list[str] = []

    title = str(
        chunk.get("title", "")
    ).strip()

    if title:
        values.append(title)

    heading_path_value = chunk.get(
        "heading_path",
        [],
    )

    if isinstance(heading_path_value, list):
        heading_path = " ".join(
            str(value).strip()
            for value in heading_path_value
            if str(value).strip()
        )
    else:
        heading_path = str(
            heading_path_value
        ).strip()

    if heading_path:
        values.append(heading_path)

    values.append(
        str(chunk["text"]).strip()
    )

    return "\n".join(values).strip()


def calculate_average_document_length(
    lexical_texts: Iterable[str],
) -> float:
    lengths = [
        max(1, len(text.split()))
        for text in lexical_texts
    ]

    if not lengths:
        return 256.0

    return max(
        1.0,
        sum(lengths) / len(lengths),
    )



def load_dense_mmodel(
        model_name: str,
        device: str | None , 
) -> SentenceTransformer:
    arguments: dict[str , any] = {}

    if device:
        arguments["device"] = device

    return SentenceTransformer(
        model_name , 
        **arguments
    )


def load_sparse_model(
    model_name: str,
    language: str,
    average_document_length: float,
) -> SparseTextEmbedding:
    return SparseTextEmbedding(
        model_name=model_name,
        language=language,
        avg_len=average_document_length,
    )


def encode_documents(
        model: SentenceTransformer,
        texts: list[str],
        batch_size: int,
) -> np.ndarray:
    if hasattr(model , "encode_document"):
        vectors = model.encode_document(
            texts,                   # the list of input strings to embed, e.g.
                                     # ["Title : Python Basics...", "Title : Data Structures..."]
                                     # each string becomes one output vector

            batch_size=32,           # how many texts are processed together in one forward pass
                                     # through the model, instead of one at a time.
                                     # e.g. if texts has 100 items, model processes them
                                     # in chunks of 32 -> 32, 32, 32, 4
                                     # bigger batch_size = faster (uses GPU/CPU parallelism better)
                                     # but uses more memory; too large can cause out-of-memory errors

            show_progress_bar=False, # if True, prints a tqdm progress bar in the console while encoding
                                     # (useful when encoding thousands of texts interactively)
                                     # set to False here to keep logs/output clean,
                                     # e.g. in production pipelines or when running silently

            convert_to_numpy=True,   # controls the OUTPUT TYPE of the function
                                     # if True  -> returns a NumPy array (easy to save, use with FAISS, etc.)
                                     # if False -> returns a PyTorch tensor instead
                                     # NumPy is usually preferred for storage/search libraries

            normalize_embeddings=True# rescales every output vector to have length (norm) = 1
                                     # (unit vector), meaning all vectors sit on the same "sphere"
                                     # WHY: once normalized, cosine similarity between two vectors
                                     # simplifies to a plain dot product, which is much faster
                                     # to compute at scale (important for vector databases/search)
)

        )
    else:
        vectors = model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

    return  np.asarray(
        vectors,
        dtype=np.float32
    )


def encode_query(
        model: SentenceTransformer,
        query: str,
                
) -> np.ndarray:
    if hasattr(model , "encode_query"):
        vector = model.encode_query(
            query,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
    else:
            vector = model.encode(
                query,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
    
    return np.asarray(
            vector,
            dtype=np.float32,
        ).reshape(-1) # this is to make same dimension with document_vectors


def create_qdrant_client(
        qdrant_path: Path,
        qdrant_url: str|None,

)-> QdrantClient:
    if qdrant_url:
        api_key = os.environ.get("QDRANT_API_KEY")

        return QdrantClient(
            url="https://31848257-7a2c-4099-950e-87e0fb063117.us-east-2-0.aws.cloud.qdrant.io:6333",
            api_key=api_key
        )

    qdrant_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    return QdrantClient(
        path=str(qdrant_path)
    )



def stable_point_id(chunk_id: str) -> str:
    return str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"rag-security-chunk:{chunk_id}",
        )
    ) 


def convert_sparse_vector(
        sparse_embedding: Any,
) -> models.SparseVector:
    indices = [
        int(value)
        for value in sparse_embedding.indices.tolist()
    ]

    values = [
        int(value)
        for value in sparse_embedding.values.tolist()
    ]

    return models.SparseVector(
        indices=indices,
        values=values
    )
    

