from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


SCHEMA_VERSION = "1.0"

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_MANIFEST_PATH = (
    PROJECT_ROOT
    / "data"
    / "manifests"
    / "documents.yaml"
)

EXTRACTED_ROOT = PROJECT_ROOT / "data" / "extracted"
PROCESSED_ROOT = PROJECT_ROOT / "data" / "processed"

# This is an approximate, model-independent tokenizer.
# Use the embedding model's real tokenizer during indexing.
TOKEN_PATTERN = re.compile(
    r"\w+|[^\w\s]",
    flags=re.UNICODE,
)

CHUNK_PROFILES: dict[str, dict[str, int]] = {
    "case_study": {
        "maximum_tokens": 450,
        "overlap_tokens": 60,
        "minimum_tokens": 60,
    },
    "technical_book": {
        "maximum_tokens": 500,
        "overlap_tokens": 75,
        "minimum_tokens": 70,
    },
    "training_book": {
        "maximum_tokens": 500,
        "overlap_tokens": 75,
        "minimum_tokens": 70,
    },
    "command_reference": {
        "maximum_tokens": 250,
        "overlap_tokens": 30,
        "minimum_tokens": 25,
    },
    "default": {
        "maximum_tokens": 450,
        "overlap_tokens": 60,
        "minimum_tokens": 60,
    },
}


@dataclass(frozen=True)
class TextAtom:
    text: str
    page_number: int
    source_block_id: str
    likely_code_block: bool

    @property
    def token_count(self) -> int:
        return approximate_token_count(self.text)


def approximate_token_count(text: str) -> int:
    return len(TOKEN_PATTERN.findall(text))


def normalize_for_hash(text: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        text.casefold(),
    ).strip()


def calculate_text_hash(text: str) -> str:
    normalized = normalize_for_hash(text)

    return hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON in {path}, "
                    f"line {line_number}: {error}"
                ) from error

    return records


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(path.name + ".tmp")

    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(
            value,
            file,
            ensure_ascii=False,
            indent=2,
        )
        file.write("\n")

    temporary_path.replace(path)


def write_jsonl(
    path: Path,
    records: list[dict[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(path.name + ".tmp")

    with temporary_path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            )
            file.write("\n")

    temporary_path.replace(path)


def load_manifest(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(
            f"Manifest not found: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        manifest = yaml.safe_load(file) or {}

    documents = manifest.get("documents", [])

    if not isinstance(documents, list) or not documents:
        raise ValueError(
            "documents.yaml must contain a "
            "non-empty 'documents' list."
        )

    return documents


def build_source_block_lookup(
    pages: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}

    for page in pages:
        page_number = int(page["page_number"])

        for block in page.get("blocks", []):
            if block.get("is_repeated_margin"):
                continue

            text = str(
                block.get("text", "")
            ).strip()

            if not text:
                continue

            block_index = int(block["block_index"])

            source_block_id = (
                f"page-{page_number:04d}/"
                f"block-{block_index:03d}"
            )

            lookup[source_block_id] = {
                "source_block_id": source_block_id,
                "page_number": page_number,
                "block_index": block_index,
                "text": text,
                "likely_code_block": bool(
                    block.get(
                        "likely_code_block",
                        False,
                    )
                ),
            }

    return lookup


def get_chunk_profile(
    document_config: dict[str, Any],
    maximum_tokens_override: int | None,
    overlap_tokens_override: int | None,
) -> dict[str, int]:
    profile_name = str(
        document_config.get(
            "chunk_profile",
            "default",
        )
    )

    profile = dict(
        CHUNK_PROFILES.get(
            profile_name,
            CHUNK_PROFILES["default"],
        )
    )

    manifest_overrides = document_config.get(
        "chunking",
        {},
    )

    if isinstance(manifest_overrides, dict):
        for property_name in (
            "maximum_tokens",
            "overlap_tokens",
            "minimum_tokens",
        ):
            if property_name in manifest_overrides:
                profile[property_name] = int(
                    manifest_overrides[
                        property_name
                    ]
                )

    if maximum_tokens_override is not None:
        profile["maximum_tokens"] = (
            maximum_tokens_override
        )

    if overlap_tokens_override is not None:
        profile["overlap_tokens"] = (
            overlap_tokens_override
        )

    if profile["maximum_tokens"] <= 0:
        raise ValueError(
            "maximum_tokens must be greater than zero"
        )

    if profile["minimum_tokens"] < 0:
        raise ValueError(
            "minimum_tokens cannot be negative"
        )

    if profile["overlap_tokens"] < 0:
        raise ValueError(
            "overlap_tokens cannot be negative"
        )

    if (
        profile["overlap_tokens"]
        >= profile["maximum_tokens"]
    ):
        raise ValueError(
            "overlap_tokens must be smaller than "
            "maximum_tokens"
        )

    return profile


def split_text_by_token_budget(
    text: str,
    maximum_tokens: int,
) -> list[str]:
    """
    Split a single oversized source block.

    Most chunks remain aligned to PDF text blocks. This
    function is only used when one block alone exceeds
    the configured maximum.
    """
    token_matches = list(
        TOKEN_PATTERN.finditer(text)
    )

    if len(token_matches) <= maximum_tokens:
        return [text]

    pieces: list[str] = []
    start_token_index = 0

    while start_token_index < len(token_matches):
        end_token_index = min(
            start_token_index + maximum_tokens,
            len(token_matches),
        )

        character_start = token_matches[
            start_token_index
        ].start()

        character_end = token_matches[
            end_token_index - 1
        ].end()

        piece = text[
            character_start:character_end
        ].strip()

        if piece:
            pieces.append(piece)

        start_token_index = end_token_index

    return pieces


def build_section_atoms(
    section: dict[str, Any],
    block_lookup: dict[str, dict[str, Any]],
    maximum_tokens: int,
) -> tuple[list[TextAtom], list[str]]:
    atoms: list[TextAtom] = []
    missing_blocks: list[str] = []

    source_block_ids = section.get(
        "source_block_ids",
        [],
    )

    for source_block_id in source_block_ids:
        block = block_lookup.get(source_block_id)

        if block is None:
            missing_blocks.append(source_block_id)
            continue

        pieces = split_text_by_token_budget(
            text=block["text"],
            maximum_tokens=maximum_tokens,
        )

        for piece in pieces:
            atoms.append(
                TextAtom(
                    text=piece,
                    page_number=block[
                        "page_number"
                    ],
                    source_block_id=(
                        source_block_id
                    ),
                    likely_code_block=block[
                        "likely_code_block"
                    ],
                )
            )

    # Fallback for a section whose source blocks could not
    # be resolved but which still has section text.
    if not atoms:
        fallback_text = str(
            section.get("text", "")
        ).strip()

        if fallback_text:
            fallback_page = int(
                section.get("page_start", 1)
            )

            pieces = split_text_by_token_budget(
                text=fallback_text,
                maximum_tokens=maximum_tokens,
            )

            for piece_index, piece in enumerate(
                pieces,
                start=1,
            ):
                atoms.append(
                    TextAtom(
                        text=piece,
                        page_number=fallback_page,
                        source_block_id=(
                            f"section-fallback/"
                            f"{piece_index:03d}"
                        ),
                        likely_code_block=bool(
                            section.get(
                                "contains_code",
                                False,
                            )
                        ),
                    )
                )

    return atoms, missing_blocks


def select_overlap_atoms(
    atoms: list[TextAtom],
    overlap_token_budget: int,
) -> list[TextAtom]:
    if overlap_token_budget <= 0:
        return []

    selected: list[TextAtom] = []
    selected_token_count = 0

    for atom in reversed(atoms):
        atom_token_count = atom.token_count

        if (
            selected_token_count
            + atom_token_count
            > overlap_token_budget
        ):
            break

        selected.append(atom)
        selected_token_count += atom_token_count

    return list(reversed(selected))


def chunk_atoms(
    atoms: list[TextAtom],
    maximum_tokens: int,
    overlap_tokens: int,
) -> list[list[TextAtom]]:
    if not atoms:
        return []

    chunks: list[list[TextAtom]] = []
    current_atoms: list[TextAtom] = []
    current_token_count = 0

    for atom in atoms:
        atom_token_count = atom.token_count

        if (
            current_atoms
            and current_token_count
            + atom_token_count
            > maximum_tokens
        ):
            chunks.append(current_atoms)

            overlap_atoms = select_overlap_atoms(
                atoms=current_atoms,
                overlap_token_budget=(
                    overlap_tokens
                ),
            )

            # Ensure that overlap plus the next atom does not
            # exceed the configured maximum.
            while (
                overlap_atoms
                and sum(
                    overlap_atom.token_count
                    for overlap_atom
                    in overlap_atoms
                )
                + atom_token_count
                > maximum_tokens
            ):
                overlap_atoms.pop(0)

            current_atoms = overlap_atoms

            current_token_count = sum(
                overlap_atom.token_count
                for overlap_atom
                in current_atoms
            )

        current_atoms.append(atom)
        current_token_count += atom_token_count

    if current_atoms:
        chunks.append(current_atoms)

    return chunks


def combine_atom_text(
    atoms: list[TextAtom],
) -> str:
    return "\n\n".join(
        atom.text.strip()
        for atom in atoms
        if atom.text.strip()
    ).strip()


def build_embedding_text(
    document_record: dict[str, Any],
    section: dict[str, Any],
    chunk_text: str,
) -> str:
    heading_path = " > ".join(
        section.get(
            "heading_path",
            [section["title"]],
        )
    )

    values = [
        f"Document: {document_record['title']}",
        f"Section: {heading_path}",
    ]

    publication_year = document_record.get(
        "publication_year"
    )

    if publication_year is not None:
        values.append(
            f"Publication year: {publication_year}"
        )

    document_type = document_record.get(
        "document_type"
    )

    if document_type:
        values.append(
            f"Document type: {document_type}"
        )

    domain = document_record.get("domain")

    if domain:
        values.append(
            f"Domain: {domain}"
        )

    values.extend(
        [
            "",
            chunk_text,
        ]
    )

    return "\n".join(values).strip()


def create_parent_record(
    section: dict[str, Any],
    document_record: dict[str, Any],
    atoms: list[TextAtom],
) -> dict[str, Any]:
    text = combine_atom_text(atoms)

    page_numbers = [
        atom.page_number for atom in atoms
    ]

    page_start = (
        min(page_numbers)
        if page_numbers
        else int(section["page_start"])
    )

    page_end = (
        max(page_numbers)
        if page_numbers
        else int(section["page_end"])
    )

    source_block_ids = list(
        dict.fromkeys(
            atom.source_block_id
            for atom in atoms
        )
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "parent_id": section["section_id"],
        "section_id": section["section_id"],
        "document_id": section["document_id"],
        "parent_section_id": section.get(
            "parent_section_id"
        ),
        "title": section["title"],
        "heading_path": section.get(
            "heading_path",
            [section["title"]],
        ),
        "level": section.get("level"),
        "page_start": page_start,
        "page_end": page_end,
        "text": text,
        "character_count": len(text),
        "token_count_approx": (
            approximate_token_count(text)
        ),
        "source_block_ids": source_block_ids,
        "contains_code": any(
            atom.likely_code_block
            for atom in atoms
        ),
        "indexable": bool(
            section.get("indexable", True)
        ),
        "freshness_warning": bool(
            document_record.get(
                "freshness_warning",
                False,
            )
        ),
        "source": section.get(
            "source",
            {
                "title": document_record["title"],
                "source_filename": document_record[
                    "source_filename"
                ],
            },
        ),
        "citation": {
            "document_title": document_record[
                "title"
            ],
            "section_title": section["title"],
            "page_start": page_start,
            "page_end": page_end,
        },
        "content_hash": calculate_text_hash(text),
    }


def create_chunk_records(
    section: dict[str, Any],
    document_record: dict[str, Any],
    chunks: list[list[TextAtom]],
    minimum_tokens: int,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    for chunk_number, atoms in enumerate(
        chunks,
        start=1,
    ):
        text = combine_atom_text(atoms)

        if not text:
            continue

        page_numbers = [
            atom.page_number for atom in atoms
        ]

        page_start = min(page_numbers)
        page_end = max(page_numbers)

        token_count = approximate_token_count(
            text
        )

        quality_flags: list[str] = []

        if token_count < minimum_tokens:
            quality_flags.append("short-chunk")

        if any(
            atom.likely_code_block
            for atom in atoms
        ):
            quality_flags.append(
                "contains-code"
            )

        source_block_ids = list(
            dict.fromkeys(
                atom.source_block_id
                for atom in atoms
            )
        )

        chunk_id = (
            f"{section['section_id']}/"
            f"chunk-{chunk_number:03d}"
        )

        records.append(
            {
                "schema_version": SCHEMA_VERSION,
                "chunk_id": chunk_id,
                "parent_id": section["section_id"],
                "section_id": section["section_id"],
                "document_id": section["document_id"],
                "chunk_number": chunk_number,
                "title": section["title"],
                "heading_path": section.get(
                    "heading_path",
                    [section["title"]],
                ),
                "text": text,
                "embedding_text": (
                    build_embedding_text(
                        document_record=(
                            document_record
                        ),
                        section=section,
                        chunk_text=text,
                    )
                ),
                "page_start": page_start,
                "page_end": page_end,
                "source_block_ids": (
                    source_block_ids
                ),
                "character_count": len(text),
                "token_count_approx": (
                    token_count
                ),
                "contains_code": any(
                    atom.likely_code_block
                    for atom in atoms
                ),
                "freshness_warning": bool(
                    document_record.get(
                        "freshness_warning",
                        False,
                    )
                ),
                "source": section.get(
                    "source"
                ),
                "citation": {
                    "document_title": (
                        document_record["title"]
                    ),
                    "section_title": (
                        section["title"]
                    ),
                    "page_start": page_start,
                    "page_end": page_end,
                },
                "quality_flags": quality_flags,
                "content_hash": (
                    calculate_text_hash(text)
                ),
            }
        )

    return records


def deduplicate_chunks(
    chunks: list[dict[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    int,
]:
    unique_chunks: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()
    duplicate_count = 0

    for chunk in chunks:
        content_hash = chunk["content_hash"]

        if content_hash in seen_hashes:
            duplicate_count += 1
            continue

        seen_hashes.add(content_hash)
        unique_chunks.append(chunk)

    return unique_chunks, duplicate_count


def build_chunk_report(
    document_id: str,
    profile: dict[str, int],
    source_sections: list[dict[str, Any]],
    parent_records: list[dict[str, Any]],
    chunk_records: list[dict[str, Any]],
    missing_blocks: list[str],
    duplicate_count: int,
) -> dict[str, Any]:
    token_counts = [
        chunk["token_count_approx"]
        for chunk in chunk_records
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "document_id": document_id,
        "profile": profile,
        "source_section_count": len(
            source_sections
        ),
        "indexable_section_count": sum(
            bool(
                section.get(
                    "indexable",
                    True,
                )
            )
            for section in source_sections
        ),
        "parent_count": len(parent_records),
        "chunk_count": len(chunk_records),
        "duplicate_chunk_count": duplicate_count,
        "missing_source_block_count": len(
            set(missing_blocks)
        ),
        "missing_source_blocks": sorted(
            set(missing_blocks)
        ),
        "minimum_chunk_tokens": (
            min(token_counts)
            if token_counts
            else 0
        ),
        "maximum_chunk_tokens": (
            max(token_counts)
            if token_counts
            else 0
        ),
        "average_chunk_tokens": (
            round(
                sum(token_counts)
                / len(token_counts),
                2,
            )
            if token_counts
            else 0
        ),
        "short_chunk_count": sum(
            "short-chunk"
            in chunk["quality_flags"]
            for chunk in chunk_records
        ),
        "chunks_with_code_count": sum(
            chunk["contains_code"]
            for chunk in chunk_records
        ),
    }


def process_document(
    document_config: dict[str, Any],
    maximum_tokens_override: int | None,
    overlap_tokens_override: int | None,
) -> None:
    document_id = document_config["id"]

    extracted_directory = (
        EXTRACTED_ROOT / document_id
    )

    processed_directory = (
        PROCESSED_ROOT / document_id
    )

    document_path = (
        extracted_directory / "document.json"
    )

    pages_path = (
        extracted_directory / "pages.jsonl"
    )

    sections_path = (
        processed_directory / "sections.jsonl"
    )

    if not document_path.exists():
        raise FileNotFoundError(
            f"Missing document metadata: "
            f"{document_path}"
        )

    if not pages_path.exists():
        raise FileNotFoundError(
            f"Missing extracted pages: "
            f"{pages_path}"
        )

    if not sections_path.exists():
        raise FileNotFoundError(
            f"Missing semantic sections: "
            f"{sections_path}"
        )

    document_record = load_json(document_path)
    pages = load_jsonl(pages_path)
    sections = load_jsonl(sections_path)

    block_lookup = build_source_block_lookup(
        pages
    )

    profile = get_chunk_profile(
        document_config=document_config,
        maximum_tokens_override=(
            maximum_tokens_override
        ),
        overlap_tokens_override=(
            overlap_tokens_override
        ),
    )

    parent_records: list[dict[str, Any]] = []
    chunk_records: list[dict[str, Any]] = []
    missing_blocks: list[str] = []

    for section in sections:
        if not section.get("indexable", True):
            continue

        atoms, section_missing_blocks = (
            build_section_atoms(
                section=section,
                block_lookup=block_lookup,
                maximum_tokens=profile[
                    "maximum_tokens"
                ],
            )
        )

        missing_blocks.extend(
            section_missing_blocks
        )

        if not atoms:
            continue

        parent_records.append(
            create_parent_record(
                section=section,
                document_record=document_record,
                atoms=atoms,
            )
        )

        section_chunks = chunk_atoms(
            atoms=atoms,
            maximum_tokens=profile[
                "maximum_tokens"
            ],
            overlap_tokens=profile[
                "overlap_tokens"
            ],
        )

        chunk_records.extend(
            create_chunk_records(
                section=section,
                document_record=document_record,
                chunks=section_chunks,
                minimum_tokens=profile[
                    "minimum_tokens"
                ],
            )
        )

    (
        chunk_records,
        duplicate_count,
    ) = deduplicate_chunks(chunk_records)

    processed_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_jsonl(
        processed_directory / "parents.jsonl",
        parent_records,
    )

    write_jsonl(
        processed_directory / "chunks.jsonl",
        chunk_records,
    )

    report = build_chunk_report(
        document_id=document_id,
        profile=profile,
        source_sections=sections,
        parent_records=parent_records,
        chunk_records=chunk_records,
        missing_blocks=missing_blocks,
        duplicate_count=duplicate_count,
    )

    write_json(
        processed_directory / "chunk-report.json",
        report,
    )

    print(
        f"[OK] {document_id}: "
        f"{len(parent_records)} parents, "
        f"{len(chunk_records)} chunks, "
        f"{duplicate_count} duplicates removed"
    )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create parent and child retrieval chunks "
            "from semantic PDF sections."
        )
    )

    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help="Path to documents.yaml",
    )

    parser.add_argument(
        "--document",
        action="append",
        dest="document_ids",
        help=(
            "Process only this document ID. "
            "May be supplied multiple times."
        ),
    )

    parser.add_argument(
        "--maximum-tokens",
        type=int,
        default=None,
        help=(
            "Override maximum chunk size for "
            "all selected documents."
        ),
    )

    parser.add_argument(
        "--overlap-tokens",
        type=int,
        default=None,
        help=(
            "Override chunk overlap for "
            "all selected documents."
        ),
    )

    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()

    manifest_path = arguments.manifest

    if not manifest_path.is_absolute():
        manifest_path = (
            PROJECT_ROOT / manifest_path
        )

    documents = load_manifest(
        manifest_path.resolve()
    )

    selected_ids = set(
        arguments.document_ids or []
    )

    if selected_ids:
        known_ids = {
            document["id"]
            for document in documents
        }

        unknown_ids = selected_ids - known_ids

        if unknown_ids:
            raise ValueError(
                "Unknown document IDs: "
                + ", ".join(sorted(unknown_ids))
            )

        documents = [
            document
            for document in documents
            if document["id"] in selected_ids
        ]

    failures: list[str] = []

    for document in documents:
        try:
            process_document(
                document_config=document,
                maximum_tokens_override=(
                    arguments.maximum_tokens
                ),
                overlap_tokens_override=(
                    arguments.overlap_tokens
                ),
            )
        except Exception as error:
            document_id = document.get(
                "id",
                "unknown",
            )

            failures.append(document_id)

            print(
                f"[ERROR] {document_id}: {error}"
            )

    if failures:
        raise SystemExit(
            "Chunk construction failed for: "
            + ", ".join(failures)
        )

    print(
        f"Chunk construction completed for "
        f"{len(documents)} document(s)."
    )


if __name__ == "__main__":
    main()