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
    chunk: dict[str, Any],
) -> str:
    embedding_text = str(
        chunk.get("embedding_text", "")
    ).strip()

    if embedding_text:
        return embedding_text

    title = str(
        chunk.get("title", "")
    ).strip()

    heading_path_value = chunk.get(
        "heading_path",
        [],
    )

    if isinstance(heading_path_value, list):
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
        values.append(f"Title: {title}")

    if heading_path:
        values.append(
            f"Section: {heading_path}"
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


# ============================================================
# Model loading
# ============================================================

def load_dense_model(
    model_name: str,
    device: str | None,
) -> SentenceTransformer:
    arguments: dict[str, Any] = {}

    if device:
        arguments["device"] = device

    return SentenceTransformer(
        model_name,
        **arguments,
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
    if hasattr(model, "encode_document"):
        vectors = model.encode_document(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
    else:
        vectors = model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

    return np.asarray(
        vectors,
        dtype=np.float32,
    )


def encode_query(
    model: SentenceTransformer,
    query: str,
) -> np.ndarray:
    if hasattr(model, "encode_query"):
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
    ).reshape(-1)


# ============================================================
# Qdrant helpers
# ============================================================

def create_qdrant_client(
    qdrant_path: Path,
    qdrant_url: str | None,
) -> QdrantClient:
    if qdrant_url:
        api_key = os.environ.get(
            "QDRANT_API_KEY"
        )

        return QdrantClient(
            url=qdrant_url,
            api_key=api_key,
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
        float(value)
        for value in sparse_embedding.values.tolist()
    ]

    return models.SparseVector(
        indices=indices,
        values=values,
    )


def create_payload(
    chunk: dict[str, Any],
) -> dict[str, Any]:
    fields = (
        "chunk_id",
        "parent_id",
        "section_id",
        "document_id",
        "chunk_number",
        "title",
        "heading_path",
        "text",
        "page_start",
        "page_end",
        "source_block_ids",
        "contains_code",
        "freshness_warning",
        "source",
        "citation",
        "quality_flags",
        "content_hash",
        "token_count_approx",
        "character_count",
    )

    payload = {
        field: chunk.get(field)
        for field in fields
        if chunk.get(field) is not None
    }

    return payload


def create_rrf_query() -> Any:
    """
    Support both the current RrfQuery API and the older
    FusionQuery representation.
    """
    try:
        return models.RrfQuery(
            rrf=models.Rrf()
        )
    except AttributeError:
        return models.FusionQuery(
            fusion=models.Fusion.RRF
        )


# ============================================================
# Index construction
# ============================================================

def build_hybrid_index(
    processed_root: Path,
    qdrant_path: Path,
    qdrant_url: str | None,
    manifest_path: Path,
    collection_name: str,
    document_ids: set[str] | None,
    dense_model_name: str,
    sparse_model_name: str,
    bm25_language: str,
    batch_size: int,
    device: str | None,
    recreate: bool,
) -> None:
    chunks, parents = load_corpus(
        processed_root=processed_root,
        selected_document_ids=document_ids,
    )

    dense_texts = [
        create_dense_text(chunk)
        for chunk in chunks
    ]

    lexical_texts = [
        create_lexical_text(chunk)
        for chunk in chunks
    ]

    average_document_length = (
        calculate_average_document_length(
            lexical_texts
        )
    )

    print(
        f"Loading dense model: {dense_model_name}"
    )

    dense_model = load_dense_model(
        model_name=dense_model_name,
        device=device,
    )

    dense_dimension_value = (
        dense_model.get_sentence_embedding_dimension()
    )

    if dense_dimension_value is None:
        sample_vector = encode_query(
            dense_model,
            "embedding dimension test",
        )
        dense_dimension = len(sample_vector)
    else:
        dense_dimension = int(
            dense_dimension_value
        )

    print(
        f"Dense vector dimension: "
        f"{dense_dimension}"
    )

    print(
        f"Loading sparse model: "
        f"{sparse_model_name}"
    )

    sparse_model = load_sparse_model(
        model_name=sparse_model_name,
        language=bm25_language,
        average_document_length=(
            average_document_length
        ),
    )

    client = create_qdrant_client(
        qdrant_path=qdrant_path,
        qdrant_url=qdrant_url,
    )

    try:
        collection_exists = (
            client.collection_exists(
                collection_name
            )
        )

        if collection_exists and not recreate:
            raise RuntimeError(
                f"Collection '{collection_name}' already "
                f"exists. Use --recreate to replace it."
            )

        if collection_exists:
            client.delete_collection(
                collection_name
            )

        client.create_collection(
            collection_name=collection_name,
            vectors_config={
                DENSE_VECTOR_NAME: (
                    models.VectorParams(
                        size=dense_dimension,
                        distance=(
                            models.Distance.COSINE
                        ),
                    )
                )
            },
            sparse_vectors_config={
                SPARSE_VECTOR_NAME: (
                    models.SparseVectorParams(
                        modifier=models.Modifier.IDF
                    )
                )
            },
        )

        total_chunks = len(chunks)

        for start in range(
            0,
            total_chunks,
            batch_size,
        ):
            end = min(
                start + batch_size,
                total_chunks,
            )

            chunk_batch = chunks[start:end]
            dense_text_batch = dense_texts[start:end]
            lexical_text_batch = lexical_texts[start:end]

            dense_vectors = encode_documents(
                model=dense_model,
                texts=dense_text_batch,
                batch_size=batch_size,
            )

            sparse_vectors = list(
                sparse_model.embed(
                    lexical_text_batch,
                    batch_size=batch_size,
                )
            )

            if len(dense_vectors) != len(chunk_batch):
                raise RuntimeError(
                    "Dense model returned an unexpected "
                    "number of vectors"
                )

            if len(sparse_vectors) != len(chunk_batch):
                raise RuntimeError(
                    "Sparse model returned an unexpected "
                    "number of vectors"
                )

            points: list[models.PointStruct] = []

            for (
                chunk,
                dense_vector,
                sparse_vector,
            ) in zip(
                chunk_batch,
                dense_vectors,
                sparse_vectors,
                strict=True,
            ):
                chunk_id = str(chunk["chunk_id"])

                points.append(
                    models.PointStruct(
                        id=stable_point_id(
                            chunk_id
                        ),
                        vector={
                            DENSE_VECTOR_NAME: (
                                dense_vector.tolist()
                            ),
                            SPARSE_VECTOR_NAME: (
                                convert_sparse_vector(
                                    sparse_vector
                                )
                            ),
                        },
                        payload=create_payload(chunk),
                    )
                )

            client.upsert(
                collection_name=collection_name,
                points=points,
                wait=True,
            )

            print(
                f"Indexed {end}/{total_chunks} chunks"
            )

        indexed_document_ids = sorted(
            {
                str(chunk["document_id"])
                for chunk in chunks
            }
        )

        report = {
            "schema_version": "1.0",
            "created_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "collection_name": collection_name,
            "dense_model": dense_model_name,
            "dense_dimension": dense_dimension,
            "sparse_model": sparse_model_name,
            "bm25_language": bm25_language,
            "bm25_average_document_length": round(
                average_document_length,
                4,
            ),
            "distance": "cosine",
            "fusion": "rrf",
            "dense_vector_name": (
                DENSE_VECTOR_NAME
            ),
            "sparse_vector_name": (
                SPARSE_VECTOR_NAME
            ),
            "document_ids": indexed_document_ids,
            "chunk_count": len(chunks),
            "parent_count": len(parents),
            "processed_root": str(processed_root),
            "qdrant_mode": (
                "server"
                if qdrant_url
                else "local"
            ),
            "qdrant_path": (
                None
                if qdrant_url
                else str(qdrant_path)
            ),
            "qdrant_url": qdrant_url,
        }

        write_json_atomic(
            manifest_path,
            report,
        )

        print()
        print("Hybrid index completed.")
        print(
            f"Collection: {collection_name}"
        )
        print(f"Chunks: {len(chunks)}")
        print(f"Parents: {len(parents)}")
        print(
            f"Manifest: {manifest_path}"
        )

    finally:
        client.close()


# ============================================================
# Retrieval result processing
# ============================================================

def create_document_filter(
    document_id: str | None,
) -> models.Filter | None:
    if not document_id:
        return None

    return models.Filter(
        must=[
            models.FieldCondition(
                key="document_id",
                match=models.MatchValue(
                    value=document_id
                ),
            )
        ]
    )


def diversify_results(
    points: list[Any],
    top_k: int,
    maximum_per_parent: int,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    parent_counts: dict[str, int] = defaultdict(int)

    for point in points:
        payload = dict(point.payload or {})

        parent_id = str(
            payload.get("parent_id", "")
        )

        if (
            parent_id
            and parent_counts[parent_id]
            >= maximum_per_parent
        ):
            continue

        if parent_id:
            parent_counts[parent_id] += 1

        results.append(
            {
                "score": float(point.score),
                **payload,
            }
        )

        if len(results) >= top_k:
            break

    return results


# ============================================================
# Parent and neighbour expansion
# ============================================================

def build_parent_lookup(
    parents: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    return {
        str(parent["parent_id"]): parent
        for parent in parents
    }


def build_neighbour_lookup(
    chunks: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    values: dict[
        str,
        list[dict[str, Any]],
    ] = defaultdict(list)

    for chunk in chunks:
        values[
            str(chunk["parent_id"])
        ].append(chunk)

    for parent_chunks in values.values():
        parent_chunks.sort(
            key=lambda chunk: int(
                chunk.get("chunk_number", 0)
            )
        )

    return dict(values)


def normalize_paragraph(text: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        text,
    ).strip().casefold()


def split_paragraphs(text: str) -> list[str]:
    return [
        paragraph.strip()
        for paragraph in re.split(
            r"\n\s*\n",
            text.strip(),
        )
        if paragraph.strip()
    ]


def merge_chunk_texts(
    chunks: list[dict[str, Any]],
) -> str:
    """
    Remove repeated paragraph boundaries caused by overlap.
    """
    merged_paragraphs: list[str] = []

    for chunk in chunks:
        incoming = split_paragraphs(
            str(chunk.get("text", ""))
        )

        if not incoming:
            continue

        maximum_overlap = min(
            len(merged_paragraphs),
            len(incoming),
        )

        overlap_size = 0

        for size in range(
            maximum_overlap,
            0,
            -1,
        ):
            existing_suffix = [
                normalize_paragraph(value)
                for value
                in merged_paragraphs[-size:]
            ]

            incoming_prefix = [
                normalize_paragraph(value)
                for value
                in incoming[:size]
            ]

            if existing_suffix == incoming_prefix:
                overlap_size = size
                break

        merged_paragraphs.extend(
            incoming[overlap_size:]
        )

    return "\n\n".join(
        merged_paragraphs
    ).strip()


def truncate_to_token_budget(
    text: str,
    token_budget: int,
) -> str:
    if token_budget <= 0:
        return ""

    matches = list(
        TOKEN_PATTERN.finditer(text)
    )

    if len(matches) <= token_budget:
        return text

    character_end = matches[
        token_budget - 1
    ].end()

    return text[:character_end].rstrip()


def create_child_context(
    hit: dict[str, Any],
) -> dict[str, Any]:
    return {
        "context_type": "child",
        "parent_id": hit.get("parent_id"),
        "document_id": hit.get("document_id"),
        "title": hit.get("title"),
        "page_start": hit.get("page_start"),
        "page_end": hit.get("page_end"),
        "chunk_ids": [hit.get("chunk_id")],
        "text": str(hit.get("text", "")),
    }


def create_parent_context(
    parent: dict[str, Any],
) -> dict[str, Any]:
    return {
        "context_type": "parent",
        "parent_id": parent.get("parent_id"),
        "document_id": parent.get("document_id"),
        "title": parent.get("title"),
        "page_start": parent.get("page_start"),
        "page_end": parent.get("page_end"),
        "chunk_ids": [],
        "text": str(parent.get("text", "")),
    }


def create_neighbour_context(
    hit: dict[str, Any],
    parent_chunks: list[dict[str, Any]],
    neighbour_window: int,
) -> dict[str, Any]:
    target_chunk_number = int(
        hit.get("chunk_number", 0)
    )

    selected_chunks = [
        chunk
        for chunk in parent_chunks
        if abs(
            int(chunk.get("chunk_number", 0))
            - target_chunk_number
        )
        <= neighbour_window
    ]

    selected_chunks.sort(
        key=lambda chunk: int(
            chunk.get("chunk_number", 0)
        )
    )

    if not selected_chunks:
        return create_child_context(hit)

    page_starts = [
        int(chunk["page_start"])
        for chunk in selected_chunks
        if chunk.get("page_start") is not None
    ]

    page_ends = [
        int(chunk["page_end"])
        for chunk in selected_chunks
        if chunk.get("page_end") is not None
    ]

    return {
        "context_type": "neighbours",
        "parent_id": hit.get("parent_id"),
        "document_id": hit.get("document_id"),
        "title": hit.get("title"),
        "page_start": (
            min(page_starts)
            if page_starts
            else hit.get("page_start")
        ),
        "page_end": (
            max(page_ends)
            if page_ends
            else hit.get("page_end")
        ),
        "chunk_ids": [
            chunk.get("chunk_id")
            for chunk in selected_chunks
        ],
        "text": merge_chunk_texts(
            selected_chunks
        ),
    }


def apply_context_budget(
    contexts: list[dict[str, Any]],
    maximum_tokens: int,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    used_tokens = 0

    for context in contexts:
        text = str(
            context.get("text", "")
        ).strip()

        if not text:
            continue

        remaining_tokens = (
            maximum_tokens - used_tokens
        )

        if remaining_tokens <= 0:
            break

        token_count = approximate_token_count(
            text
        )

        if token_count > remaining_tokens:
            if remaining_tokens < 50:
                break

            text = truncate_to_token_budget(
                text,
                remaining_tokens,
            )

            context = dict(context)
            context["text"] = text
            context["truncated"] = True
            token_count = approximate_token_count(
                text
            )
        else:
            context = dict(context)
            context["truncated"] = False

        context["token_count_approx"] = (
            token_count
        )

        selected.append(context)
        used_tokens += token_count

    return selected


def build_expanded_contexts(
    hits: list[dict[str, Any]],
    parents_by_id: dict[
        str,
        dict[str, Any],
    ],
    chunks_by_parent: dict[
        str,
        list[dict[str, Any]],
    ],
    mode: str,
    neighbour_window: int,
    parent_token_limit: int,
    context_token_budget: int,
) -> list[dict[str, Any]]:
    if mode == "none":
        return []

    if mode == "child":
        contexts = [
            create_child_context(hit)
            for hit in hits
        ]

        return apply_context_budget(
            contexts,
            context_token_budget,
        )

    contexts: list[dict[str, Any]] = []
    used_parent_ids: set[str] = set()

    for hit in hits:
        parent_id = str(
            hit.get("parent_id", "")
        )

        if parent_id in used_parent_ids:
            continue

        if parent_id:
            used_parent_ids.add(parent_id)

        parent = parents_by_id.get(parent_id)
        parent_chunks = chunks_by_parent.get(
            parent_id,
            [],
        )

        if mode == "parent":
            if parent is not None:
                context = create_parent_context(
                    parent
                )
            else:
                context = create_child_context(
                    hit
                )

        elif mode == "neighbors":
            context = create_neighbour_context(
                hit=hit,
                parent_chunks=parent_chunks,
                neighbour_window=(
                    neighbour_window
                ),
            )

        elif mode == "auto":
            parent_tokens = (
                int(
                    parent.get(
                        "token_count_approx",
                        0,
                    )
                )
                if parent
                else 0
            )

            if (
                parent is not None
                and parent_tokens > 0
                and parent_tokens
                <= parent_token_limit
            ):
                context = create_parent_context(
                    parent
                )
            else:
                context = create_neighbour_context(
                    hit=hit,
                    parent_chunks=parent_chunks,
                    neighbour_window=(
                        neighbour_window
                    ),
                )

        else:
            raise ValueError(
                f"Unknown context mode: {mode}"
            )

        contexts.append(context)

    return apply_context_budget(
        contexts,
        context_token_budget,
    )


# ============================================================
# Hybrid search
# ============================================================

def hybrid_search(
    processed_root: Path,
    qdrant_path: Path,
    qdrant_url: str | None,
    manifest_path: Path,
    collection_name: str,
    query: str,
    document_id: str | None,
    top_k: int,
    candidate_limit: int,
    maximum_per_parent: int,
    context_mode: str,
    neighbour_window: int,
    parent_token_limit: int,
    context_token_budget: int,
    device: str | None,
) -> dict[str, Any]:
    if not query.strip():
        raise ValueError(
            "Search query cannot be empty"
        )

    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Index manifest not found: "
            f"{manifest_path}. Run the index command first."
        )

    manifest = load_json(manifest_path)

    dense_model_name = str(
        manifest["dense_model"]
    )

    sparse_model_name = str(
        manifest["sparse_model"]
    )

    bm25_language = str(
        manifest.get(
            "bm25_language",
            "english",
        )
    )

    average_document_length = float(
        manifest.get(
            "bm25_average_document_length",
            256.0,
        )
    )

    print(
        f"Loading dense model: {dense_model_name}",
        file=os.sys.stderr,
    )

    dense_model = load_dense_model(
        model_name=dense_model_name,
        device=device,
    )

    sparse_model = load_sparse_model(
        model_name=sparse_model_name,
        language=bm25_language,
        average_document_length=(
            average_document_length
        ),
    )

    dense_query_vector = encode_query(
        dense_model,
        query,
    )

    sparse_query_embedding = next(
        iter(
            sparse_model.query_embed(query)
        )
    )

    query_filter = create_document_filter(
        document_id
    )

    prefetches: list[models.Prefetch] = [
        models.Prefetch(
            query=dense_query_vector.tolist(),
            using=DENSE_VECTOR_NAME,
            filter=query_filter,
            limit=candidate_limit,
        )
    ]

    if len(sparse_query_embedding.indices) > 0:
        prefetches.append(
            models.Prefetch(
                query=convert_sparse_vector(
                    sparse_query_embedding
                ),
                using=SPARSE_VECTOR_NAME,
                filter=query_filter,
                limit=candidate_limit,
            )
        )

    client = create_qdrant_client(
        qdrant_path=qdrant_path,
        qdrant_url=qdrant_url,
    )

    try:
        if not client.collection_exists(
            collection_name
        ):
            raise RuntimeError(
                f"Qdrant collection "
                f"'{collection_name}' does not exist"
            )

        response = client.query_points(
            collection_name=collection_name,
            prefetch=prefetches,
            query=create_rrf_query(),
            query_filter=query_filter,
            limit=candidate_limit,
            with_payload=True,
            with_vectors=False,
        )

        hits = diversify_results(
            points=list(response.points),
            top_k=top_k,
            maximum_per_parent=(
                maximum_per_parent
            ),
        )

    finally:
        client.close()

    selected_document_ids = (
        {document_id}
        if document_id
        else None
    )

    chunks, parents = load_corpus(
        processed_root=processed_root,
        selected_document_ids=(
            selected_document_ids
        ),
    )

    parents_by_id = build_parent_lookup(
        parents
    )

    chunks_by_parent = build_neighbour_lookup(
        chunks
    )

    contexts = build_expanded_contexts(
        hits=hits,
        parents_by_id=parents_by_id,
        chunks_by_parent=chunks_by_parent,
        mode=context_mode,
        neighbour_window=neighbour_window,
        parent_token_limit=parent_token_limit,
        context_token_budget=(
            context_token_budget
        ),
    )

    return {
        "query": query,
        "retrieval": {
            "type": "hybrid",
            "dense_model": dense_model_name,
            "sparse_model": sparse_model_name,
            "fusion": "rrf",
            "candidate_limit": candidate_limit,
            "top_k": top_k,
            "maximum_per_parent": (
                maximum_per_parent
            ),
            "document_filter": document_id,
        },
        "hits": hits,
        "contexts": contexts,
    }


# ============================================================
# Output
# ============================================================

def print_search_result(
    result: dict[str, Any],
) -> None:
    print()
    print(f"Query: {result['query']}")
    print()

    hits = result["hits"]

    if not hits:
        print("No matching chunks were found.")
        return

    print("Hybrid retrieval results")
    print("========================")

    for rank, hit in enumerate(
        hits,
        start=1,
    ):
        print()
        print(
            f"{rank}. {hit.get('title', 'Untitled')}"
        )
        print(
            f"   score: {hit.get('score', 0.0):.6f}"
        )
        print(
            f"   chunk: {hit.get('chunk_id')}"
        )
        print(
            f"   parent: {hit.get('parent_id')}"
        )
        print(
            f"   pages: "
            f"{hit.get('page_start')}–"
            f"{hit.get('page_end')}"
        )

        text = str(
            hit.get("text", "")
        ).strip()

        preview = re.sub(
            r"\s+",
            " ",
            text,
        )

        if len(preview) > 300:
            preview = preview[:297] + "..."

        print(f"   preview: {preview}")

    contexts = result.get("contexts", [])

    if contexts:
        print()
        print("Expanded contexts")
        print("=================")

        for number, context in enumerate(
            contexts,
            start=1,
        ):
            print()
            print(
                f"Context {number}: "
                f"{context.get('title', 'Untitled')}"
            )
            print(
                f"Type: "
                f"{context.get('context_type')}"
            )
            print(
                f"Pages: "
                f"{context.get('page_start')}–"
                f"{context.get('page_end')}"
            )
            print(
                f"Parent: "
                f"{context.get('parent_id')}"
            )
            print()
            print(context.get("text", ""))


# ============================================================
# Command-line parsing
# ============================================================

def add_common_connection_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "--qdrant-path",
        type=Path,
        default=DEFAULT_QDRANT_PATH,
        help=(
            "Local Qdrant storage directory. "
            "Ignored when --qdrant-url is supplied."
        ),
    )

    parser.add_argument(
        "--qdrant-url",
        default=None,
        help=(
            "Qdrant server URL. The API key is read "
            "from QDRANT_API_KEY."
        ),
    )

    parser.add_argument(
        "--collection",
        default=DEFAULT_COLLECTION_NAME,
        help="Qdrant collection name",
    )

    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_INDEX_MANIFEST,
        help="Hybrid index manifest path",
    )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build and search a dense + BM25 "
            "Qdrant hybrid index."
        )
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    index_parser = subparsers.add_parser(
        "index",
        help="Build the hybrid index",
    )

    add_common_connection_arguments(
        index_parser
    )

    index_parser.add_argument(
        "--processed-root",
        type=Path,
        default=DEFAULT_PROCESSED_ROOT,
    )

    index_parser.add_argument(
        "--document",
        action="append",
        dest="document_ids",
        help=(
            "Index only this document ID. "
            "May be supplied multiple times."
        ),
    )

    index_parser.add_argument(
        "--dense-model",
        default=DENSE_MODEL_NAME,
    )

    index_parser.add_argument(
        "--sparse-model",
        default=SPARSE_MODEL_NAME,
    )

    index_parser.add_argument(
        "--bm25-language",
        default="english",
    )

    index_parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
    )

    index_parser.add_argument(
        "--device",
        default=None,
        help=(
            "SentenceTransformer device, for example "
            "'cpu', 'cuda', or 'cuda:0'."
        ),
    )

    index_parser.add_argument(
        "--recreate",
        action="store_true",
        help=(
            "Delete and rebuild the existing collection"
        ),
    )

    search_parser = subparsers.add_parser(
        "search",
        help="Run hybrid retrieval",
    )

    add_common_connection_arguments(
        search_parser
    )

    search_parser.add_argument(
        "--processed-root",
        type=Path,
        default=DEFAULT_PROCESSED_ROOT,
    )

    search_parser.add_argument(
        "--query",
        required=True,
    )

    search_parser.add_argument(
        "--document",
        default=None,
        help="Optional document_id filter",
    )

    search_parser.add_argument(
        "--top-k",
        type=int,
        default=8,
    )

    search_parser.add_argument(
        "--candidate-limit",
        type=int,
        default=30,
    )

    search_parser.add_argument(
        "--max-per-parent",
        type=int,
        default=2,
    )

    search_parser.add_argument(
        "--context-mode",
        choices=(
            "none",
            "child",
            "neighbors",
            "parent",
            "auto",
        ),
        default="auto",
    )

    search_parser.add_argument(
        "--neighbor-window",
        type=int,
        default=1,
    )

    search_parser.add_argument(
        "--parent-token-limit",
        type=int,
        default=1400,
        help=(
            "In auto mode, use the complete parent "
            "only when it is no larger than this."
        ),
    )

    search_parser.add_argument(
        "--context-token-budget",
        type=int,
        default=6000,
    )

    search_parser.add_argument(
        "--device",
        default=None,
    )

    search_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON",
    )

    return parser.parse_args()


# ============================================================
# Main
# ============================================================

def main() -> None:
    arguments = parse_arguments()

    processed_root = resolve_project_path(
        arguments.processed_root
    )

    qdrant_path = resolve_project_path(
        arguments.qdrant_path
    )

    manifest_path = resolve_project_path(
        arguments.manifest
    )

    if arguments.command == "index":
        if arguments.batch_size <= 0:
            raise ValueError(
                "batch-size must be greater than zero"
            )

        build_hybrid_index(
            processed_root=processed_root,
            qdrant_path=qdrant_path,
            qdrant_url=arguments.qdrant_url,
            manifest_path=manifest_path,
            collection_name=arguments.collection,
            document_ids=set(
                arguments.document_ids or []
            )
            or None,
            dense_model_name=(
                arguments.dense_model
            ),
            sparse_model_name=(
                arguments.sparse_model
            ),
            bm25_language=(
                arguments.bm25_language
            ),
            batch_size=arguments.batch_size,
            device=arguments.device,
            recreate=arguments.recreate,
        )

        return

    if arguments.top_k <= 0:
        raise ValueError(
            "top-k must be greater than zero"
        )

    if arguments.candidate_limit < arguments.top_k:
        raise ValueError(
            "candidate-limit must be at least top-k"
        )

    if arguments.max_per_parent <= 0:
        raise ValueError(
            "max-per-parent must be greater than zero"
        )

    result = hybrid_search(
        processed_root=processed_root,
        qdrant_path=qdrant_path,
        qdrant_url=arguments.qdrant_url,
        manifest_path=manifest_path,
        collection_name=arguments.collection,
        query=arguments.query,
        document_id=arguments.document,
        top_k=arguments.top_k,
        candidate_limit=(
            arguments.candidate_limit
        ),
        maximum_per_parent=(
            arguments.max_per_parent
        ),
        context_mode=arguments.context_mode,
        neighbour_window=(
            arguments.neighbor_window
        ),
        parent_token_limit=(
            arguments.parent_token_limit
        ),
        context_token_budget=(
            arguments.context_token_budget
        ),
        device=arguments.device,
    )

    if arguments.json:
        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print_search_result(result)


if __name__ == "__main__":
    main()