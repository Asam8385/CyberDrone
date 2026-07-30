from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import yaml


SCHEMA_VERSION = "1.0"

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DEFAULT_MANIFEST_PATH = (
    PROJECT_ROOT
    / "data"
    / "manifests"
    / "documents.yaml"
)

EXTRACTED_ROOT = PROJECT_ROOT / "data" / "extracted"
PROCESSED_ROOT = PROJECT_ROOT / "data" / "processed"

NON_INDEXABLE_TITLES = (
    re.compile(r"^cover$", re.I),
    re.compile(r"^copyright$", re.I),
    re.compile(r"^credits$", re.I),
    re.compile(r"^brief contents$", re.I),
    re.compile(r"^contents in detail$", re.I),
    re.compile(r"^table of contents$", re.I),
    re.compile(r"^foreword.*$", re.I),
    re.compile(r"^acknowledg(e)?ments$", re.I),
    re.compile(r"^about the author$", re.I),
    re.compile(r"^about the reviewer$", re.I),
    re.compile(r"^index$", re.I),
    re.compile(r"^www\..*$", re.I),
)

TITLE_PREFIX_PATTERNS = (
    re.compile(
        r"^\s*chapter\s+\d+\s*[:.-]?\s*",
        re.I,
    ),
    re.compile(
        r"^\s*appendix\s+[a-z0-9]+\s*[:.-]?\s*",
        re.I,
    ),
    re.compile(
        r"^\s*part\s+[ivxlcdm0-9]+\s*[:.-]?\s*",
        re.I,
    ),
)


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
    with path.open("r", encoding="utf-8") as file:
        manifest = yaml.safe_load(file) or {}

    documents = manifest.get("documents", [])

    if not documents:
        raise ValueError(
            "No documents were found in documents.yaml"
        )

    return documents


def collapse_whitespace(text: str) -> str:
    text = text.replace("\u00ad", "")
    text = text.replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def normalize_heading(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = collapse_whitespace(text)
    text = text.casefold()
    text = re.sub(r"[^\w]+", " ", text)
    return collapse_whitespace(text)


def heading_skeleton(text: str) -> str:
    normalized = normalize_heading(text)
    return re.sub(r"[^a-z0-9]+", "", normalized)


def slugify(text: str, maximum_length: int = 70) -> str:
    value = normalize_heading(text)
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")

    if not value:
        value = "section"

    return value[:maximum_length].rstrip("-")


def create_title_variants(title: str) -> list[str]:
    variants = {collapse_whitespace(title)}

    for pattern in TITLE_PREFIX_PATTERNS:
        stripped = pattern.sub("", title).strip()

        if stripped:
            variants.add(stripped)

    return sorted(variants)


def calculate_heading_similarity(
    expected_title: str,
    candidate_text: str,
) -> float:
    candidate_text = collapse_whitespace(candidate_text)

    if not candidate_text:
        return 0.0

    best_score = 0.0

    for variant in create_title_variants(expected_title):
        variant_normalized = normalize_heading(variant)
        candidate_normalized = normalize_heading(
            candidate_text
        )

        variant_skeleton = heading_skeleton(variant)
        candidate_skeleton = heading_skeleton(
            candidate_text
        )

        if not variant_skeleton or not candidate_skeleton:
            continue

        if variant_skeleton == candidate_skeleton:
            return 1.0

        if (
            candidate_skeleton.startswith(variant_skeleton)
            and len(candidate_skeleton)
            <= len(variant_skeleton) * 2
        ):
            best_score = max(best_score, 0.96)

        if (
            variant_skeleton in candidate_skeleton
            and len(candidate_skeleton)
            <= len(variant_skeleton) * 2
        ):
            best_score = max(best_score, 0.92)

        skeleton_similarity = SequenceMatcher(
            None,
            variant_skeleton,
            candidate_skeleton,
        ).ratio()

        word_similarity = SequenceMatcher(
            None,
            variant_normalized,
            candidate_normalized,
        ).ratio()

        expected_words = set(variant_normalized.split())
        candidate_words = set(candidate_normalized.split())

        if expected_words and candidate_words:
            word_overlap = len(
                expected_words & candidate_words
            ) / len(expected_words | candidate_words)
        else:
            word_overlap = 0.0

        score = max(
            skeleton_similarity,
            word_similarity,
            word_overlap,
        )

        best_score = max(best_score, score)

    return round(best_score, 4)


def collect_block_font_statistics(
    block: dict[str, Any],
) -> dict[str, Any]:
    total_characters = 0
    bold_characters = 0
    monospaced_characters = 0
    maximum_font_size = 0.0
    font_weights: Counter[float] = Counter()

    for line in block.get("lines", []):
        for span in line.get("spans", []):
            text = str(span.get("text", ""))
            character_count = len(text.strip())

            if character_count == 0:
                continue

            font_size = float(span.get("font_size", 0.0))
            rounded_size = round(font_size * 2) / 2

            total_characters += character_count
            maximum_font_size = max(
                maximum_font_size,
                font_size,
            )

            font_weights[rounded_size] += character_count

            if span.get("is_bold"):
                bold_characters += character_count

            if span.get("is_monospaced"):
                monospaced_characters += character_count

    bold_ratio = (
        bold_characters / total_characters
        if total_characters
        else 0.0
    )

    monospaced_ratio = (
        monospaced_characters / total_characters
        if total_characters
        else 0.0
    )

    return {
        "maximum_font_size": maximum_font_size,
        "bold_ratio": bold_ratio,
        "monospaced_ratio": monospaced_ratio,
        "font_weights": font_weights,
    }


def flatten_pages(
    pages: list[dict[str, Any]],
    content_start_page: int,
    content_end_page: int | None,
) -> tuple[
    list[dict[str, Any]],
    dict[int, dict[str, Any]],
]:
    units: list[dict[str, Any]] = []
    pages_by_number: dict[int, dict[str, Any]] = {}

    sorted_pages = sorted(
        pages,
        key=lambda page: page["page_number"],
    )

    for page in sorted_pages:
        page_number = int(page["page_number"])
        pages_by_number[page_number] = page

        if page_number < content_start_page:
            continue

        if (
            content_end_page is not None
            and page_number > content_end_page
        ):
            continue

        for block in page.get("blocks", []):
            if block.get("is_repeated_margin"):
                continue

            text = str(block.get("text", "")).strip()

            if not text:
                continue

            statistics = collect_block_font_statistics(
                block
            )

            units.append(
                {
                    "global_index": len(units),
                    "source_block_id": (
                        f"page-{page_number:04d}/"
                        f"block-{int(block['block_index']):03d}"
                    ),
                    "page_number": page_number,
                    "block_index": int(
                        block["block_index"]
                    ),
                    "text": text,
                    "line_count": len(
                        block.get("lines", [])
                    ),
                    "bbox": block.get("bbox", []),
                    "likely_code_block": bool(
                        block.get(
                            "likely_code_block",
                            False,
                        )
                    ),
                    "maximum_font_size": statistics[
                        "maximum_font_size"
                    ],
                    "bold_ratio": statistics["bold_ratio"],
                    "monospaced_ratio": statistics[
                        "monospaced_ratio"
                    ],
                    "font_weights": statistics[
                        "font_weights"
                    ],
                }
            )

    return units, pages_by_number


def detect_body_font_size(
    units: list[dict[str, Any]],
) -> float:
    weights: Counter[float] = Counter()

    for unit in units:
        if unit["likely_code_block"]:
            continue

        for font_size, count in unit[
            "font_weights"
        ].items():
            if 6.0 <= font_size <= 16.0:
                weights[font_size] += count

    if not weights:
        return 10.0

    return float(weights.most_common(1)[0][0])


def is_numeric_chapter_marker(text: str) -> bool:
    value = collapse_whitespace(text)

    return bool(
        re.fullmatch(
            r"(?:\d+|[ivxlcdm]+)",
            value,
            flags=re.I,
        )
    )


def is_heading_candidate(
    unit: dict[str, Any],
    body_font_size: float,
) -> bool:
    text = collapse_whitespace(unit["text"])

    if len(text) < 2 or len(text) > 180:
        return False

    if unit["likely_code_block"]:
        return False

    if is_numeric_chapter_marker(text):
        return False

    if "http://" in text.casefold():
        return False

    if "https://" in text.casefold():
        return False

    word_count = len(text.split())

    if word_count > 22:
        return False

    if unit["line_count"] > 4:
        return False

    if (
        text.endswith(".")
        and not text.casefold().startswith("chapter ")
    ):
        return False

    maximum_size = unit["maximum_font_size"]
    bold_ratio = unit["bold_ratio"]

    explicit_heading = bool(
        re.match(
            r"^(?:chapter|part|appendix)\s+",
            text,
            flags=re.I,
        )
    )

    large_font = (
        maximum_size >= body_font_size * 1.15
    )

    bold_heading = (
        bold_ratio >= 0.65
        and maximum_size >= body_font_size * 0.95
    )

    return explicit_heading or large_font or bold_heading


def infer_heading_level(
    unit: dict[str, Any],
    units: list[dict[str, Any]],
    body_font_size: float,
) -> int:
    text = collapse_whitespace(unit["text"])

    if re.match(
        r"^(?:chapter|part|appendix)\s+",
        text,
        flags=re.I,
    ):
        return 1

    previous_index = unit["global_index"] - 1

    if previous_index >= 0:
        previous = units[previous_index]

        if (
            previous["page_number"]
            == unit["page_number"]
            and is_numeric_chapter_marker(
                previous["text"]
            )
            and previous["maximum_font_size"]
            >= body_font_size * 3
        ):
            return 1

    maximum_size = unit["maximum_font_size"]

    if maximum_size >= body_font_size * 1.45:
        return 1

    if maximum_size >= body_font_size * 1.15:
        return 2

    return 3


def create_unit_page_map(
    units: list[dict[str, Any]],
) -> dict[int, list[dict[str, Any]]]:
    mapping: dict[int, list[dict[str, Any]]] = (
        defaultdict(list)
    )

    for unit in units:
        mapping[unit["page_number"]].append(unit)

    return dict(mapping)


def find_toc_anchor(
    toc_entry: dict[str, Any],
    units_by_page: dict[int, list[dict[str, Any]]],
    body_font_size: float,
    minimum_global_index: int,
    used_indices: set[int],
) -> tuple[dict[str, Any] | None, float, str]:
    expected_page = int(toc_entry["page_number"])
    expected_title = str(toc_entry["title"])

    best_unit: dict[str, Any] | None = None
    best_score = 0.0

    page_offsets = (0, 1, -1)

    for page_offset in page_offsets:
        page_number = expected_page + page_offset

        for unit in units_by_page.get(page_number, []):
            global_index = unit["global_index"]

            if global_index < minimum_global_index:
                continue

            if global_index in used_indices:
                continue

            score = calculate_heading_similarity(
                expected_title,
                unit["text"],
            )

            if is_heading_candidate(
                unit,
                body_font_size,
            ):
                score = min(1.0, score + 0.03)

            score -= abs(page_offset) * 0.04

            if score > best_score:
                best_score = score
                best_unit = unit

    if best_unit is not None and best_score >= 0.64:
        return (
            best_unit,
            round(best_score, 4),
            "toc-text-anchor",
        )

    fallback_candidates: list[dict[str, Any]] = []

    for page_offset in (0, 1, 2):
        page_number = expected_page + page_offset

        for unit in units_by_page.get(page_number, []):
            if unit["global_index"] < minimum_global_index:
                continue

            if unit["global_index"] in used_indices:
                continue

            fallback_candidates.append(unit)

    heading_candidates = [
        unit
        for unit in fallback_candidates
        if is_heading_candidate(
            unit,
            body_font_size,
        )
    ]

    if heading_candidates:
        return (
            heading_candidates[0],
            0.0,
            "toc-heading-fallback",
        )

    if fallback_candidates:
        return (
            fallback_candidates[0],
            0.0,
            "toc-page-fallback",
        )

    return None, 0.0, "unresolved"


def build_toc_events(
    toc: list[dict[str, Any]],
    units: list[dict[str, Any]],
    body_font_size: float,
) -> tuple[
    list[dict[str, Any]],
    list[str],
]:
    units_by_page = create_unit_page_map(units)
    events: list[dict[str, Any]] = []
    warnings: list[str] = []
    used_indices: set[int] = set()
    minimum_global_index = 0

    for toc_entry in toc:
        anchor, score, method = find_toc_anchor(
            toc_entry=toc_entry,
            units_by_page=units_by_page,
            body_font_size=body_font_size,
            minimum_global_index=minimum_global_index,
            used_indices=used_indices,
        )

        if anchor is None:
            warnings.append(
                f"Could not resolve TOC entry "
                f"'{toc_entry['title']}' on page "
                f"{toc_entry['page_number']}."
            )
            continue

        global_index = anchor["global_index"]
        used_indices.add(global_index)
        minimum_global_index = global_index + 1

        events.append(
            {
                "event_id": toc_entry["toc_id"],
                "parent_event_id": toc_entry.get(
                    "parent_toc_id"
                ),
                "title": collapse_whitespace(
                    toc_entry["title"]
                ),
                "level": int(toc_entry["level"]),
                "anchor_index": global_index,
                "anchor_page": anchor["page_number"],
                "anchor_block_id": anchor[
                    "source_block_id"
                ],
                "anchor_score": score,
                "detection_method": method,
            }
        )

    return events, warnings


def find_manual_chapter_anchor(
    hint: dict[str, Any],
    units_by_page: dict[int, list[dict[str, Any]]],
    body_font_size: float,
) -> dict[str, Any] | None:
    page_number = int(hint["page_number"])

    candidates = [
        unit
        for unit in units_by_page.get(page_number, [])
        if not is_numeric_chapter_marker(unit["text"])
    ]

    if not candidates:
        return None

    heading_candidates = [
        unit
        for unit in candidates
        if is_heading_candidate(
            unit,
            body_font_size,
        )
    ]

    if heading_candidates:
        return max(
            heading_candidates,
            key=lambda unit: (
                unit["maximum_font_size"],
                unit["bold_ratio"],
                -unit["block_index"],
            ),
        )

    return candidates[0]


def build_font_events(
    document_config: dict[str, Any],
    units: list[dict[str, Any]],
    body_font_size: float,
) -> tuple[
    list[dict[str, Any]],
    list[str],
]:
    units_by_page = create_unit_page_map(units)
    warnings: list[str] = []
    events_by_anchor: dict[int, dict[str, Any]] = {}

    for unit in units:
        if not is_heading_candidate(
            unit,
            body_font_size,
        ):
            continue

        level = infer_heading_level(
            unit=unit,
            units=units,
            body_font_size=body_font_size,
        )

        events_by_anchor[unit["global_index"]] = {
            "event_id": None,
            "parent_event_id": None,
            "title": collapse_whitespace(unit["text"]),
            "level": level,
            "anchor_index": unit["global_index"],
            "anchor_page": unit["page_number"],
            "anchor_block_id": unit[
                "source_block_id"
            ],
            "anchor_score": 1.0,
            "detection_method": "font-heading",
        }

    for hint_index, hint in enumerate(
        document_config.get("chapter_starts", []),
        start=1,
    ):
        anchor = find_manual_chapter_anchor(
            hint=hint,
            units_by_page=units_by_page,
            body_font_size=body_font_size,
        )

        if anchor is None:
            warnings.append(
                f"Could not resolve manual chapter "
                f"'{hint['title']}' on page "
                f"{hint['page_number']}."
            )
            continue

        events_by_anchor[anchor["global_index"]] = {
            "event_id": f"manual-{hint_index:04d}",
            "parent_event_id": None,
            "title": collapse_whitespace(
                hint["title"]
            ),
            "level": int(hint.get("level", 1)),
            "anchor_index": anchor["global_index"],
            "anchor_page": anchor["page_number"],
            "anchor_block_id": anchor[
                "source_block_id"
            ],
            "anchor_score": 1.0,
            "detection_method": "manual-chapter-anchor",
        }

    events = sorted(
        events_by_anchor.values(),
        key=lambda event: event["anchor_index"],
    )

    level_stack: dict[int, str] = {}

    for event_index, event in enumerate(
        events,
        start=1,
    ):
        if not event["event_id"]:
            event["event_id"] = (
                f"font-{event_index:04d}"
            )

        level = event["level"]

        event["parent_event_id"] = (
            level_stack.get(level - 1)
            if level > 1
            else None
        )

        level_stack[level] = event["event_id"]

        for existing_level in list(level_stack):
            if existing_level > level:
                del level_stack[existing_level]

    return events, warnings


def build_heading_path(
    event: dict[str, Any],
    events_by_id: dict[str, dict[str, Any]],
) -> list[str]:
    titles: list[str] = []
    current: dict[str, Any] | None = event
    visited: set[str] = set()

    while current is not None:
        event_id = current["event_id"]

        if event_id in visited:
            break

        visited.add(event_id)
        titles.append(current["title"])

        parent_id = current.get("parent_event_id")

        if not parent_id:
            break

        current = events_by_id.get(parent_id)

    return list(reversed(titles))


def is_indexable_title(title: str) -> bool:
    normalized = collapse_whitespace(title)

    return not any(
        pattern.match(normalized)
        for pattern in NON_INDEXABLE_TITLES
    )


def collect_table_ids(
    pages_by_number: dict[int, dict[str, Any]],
    page_start: int,
    page_end: int,
) -> list[str]:
    table_ids: list[str] = []

    for page_number in range(
        page_start,
        page_end + 1,
    ):
        page = pages_by_number.get(page_number)

        if not page:
            continue

        table_ids.extend(
            page.get("table_ids", [])
        )

    return list(dict.fromkeys(table_ids))


def build_sections_from_events(
    document_record: dict[str, Any],
    events: list[dict[str, Any]],
    units: list[dict[str, Any]],
    pages_by_number: dict[int, dict[str, Any]],
    minimum_section_characters: int,
) -> list[dict[str, Any]]:
    if not events:
        return []

    events = sorted(
        events,
        key=lambda event: event["anchor_index"],
    )

    events_by_id = {
        event["event_id"]: event
        for event in events
    }

    section_ids_by_event: dict[str, str] = {}

    for section_number, event in enumerate(
        events,
        start=1,
    ):
        section_ids_by_event[event["event_id"]] = (
            f"{document_record['document_id']}/"
            f"{section_number:04d}-"
            f"{slugify(event['title'])}"
        )

    sections: list[dict[str, Any]] = []

    for event_index, event in enumerate(events):
        start_index = int(event["anchor_index"])

        if event_index + 1 < len(events):
            end_index = int(
                events[event_index + 1][
                    "anchor_index"
                ]
            )
        else:
            end_index = len(units)

        if end_index <= start_index:
            continue

        section_units = units[
            start_index:end_index
        ]

        if not section_units:
            continue

        text = "\n\n".join(
            unit["text"] for unit in section_units
        ).strip()

        page_start = min(
            unit["page_number"]
            for unit in section_units
        )

        page_end = max(
            unit["page_number"]
            for unit in section_units
        )

        parent_event_id = event.get(
            "parent_event_id"
        )

        parent_section_id = (
            section_ids_by_event.get(parent_event_id)
            if parent_event_id
            else None
        )

        heading_path = build_heading_path(
            event=event,
            events_by_id=events_by_id,
        )

        quality_flags: list[str] = []

        if event["detection_method"].endswith(
            "fallback"
        ):
            quality_flags.append(
                "fallback-heading-anchor"
            )

        if len(text) < minimum_section_characters:
            quality_flags.append("short-section")

        if event["anchor_score"] < 0.64:
            quality_flags.append(
                "low-anchor-confidence"
            )

        indexable = (
            is_indexable_title(event["title"])
            and len(text)
            >= minimum_section_characters
        )

        section_id = section_ids_by_event[
            event["event_id"]
        ]

        sections.append(
            {
                "schema_version": SCHEMA_VERSION,
                "section_id": section_id,
                "document_id": document_record[
                    "document_id"
                ],
                "parent_section_id": (
                    parent_section_id
                ),
                "section_number": len(sections) + 1,
                "title": event["title"],
                "heading_path": heading_path,
                "level": event["level"],
                "page_start": page_start,
                "page_end": page_end,
                "text": text,
                "character_count": len(text),
                "word_count": len(text.split()),
                "source_block_ids": [
                    unit["source_block_id"]
                    for unit in section_units
                ],
                "table_ids": collect_table_ids(
                    pages_by_number=pages_by_number,
                    page_start=page_start,
                    page_end=page_end,
                ),
                "contains_code": any(
                    unit["likely_code_block"]
                    for unit in section_units
                ),
                "indexable": indexable,
                "detection": {
                    "method": event[
                        "detection_method"
                    ],
                    "anchor_page": event[
                        "anchor_page"
                    ],
                    "anchor_block_id": event[
                        "anchor_block_id"
                    ],
                    "anchor_score": event[
                        "anchor_score"
                    ],
                },
                "source": {
                    "title": document_record[
                        "title"
                    ],
                    "author": document_record.get(
                        "author"
                    ),
                    "publication_year": (
                        document_record.get(
                            "publication_year"
                        )
                    ),
                    "source_filename": (
                        document_record[
                            "source_filename"
                        ]
                    ),
                    "source_sha256": (
                        document_record[
                            "source_sha256"
                        ]
                    ),
                },
                "citation": {
                    "document_title": (
                        document_record["title"]
                    ),
                    "section_title": event["title"],
                    "page_start": page_start,
                    "page_end": page_end,
                },
                "quality_flags": quality_flags,
            }
        )

    return sections


def build_section_report(
    document_id: str,
    detection_mode: str,
    body_font_size: float,
    sections: list[dict[str, Any]],
    event_count: int,
    warnings: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "document_id": document_id,
        "detection_mode": detection_mode,
        "body_font_size": body_font_size,
        "heading_event_count": event_count,
        "section_count": len(sections),
        "indexable_section_count": sum(
            section["indexable"]
            for section in sections
        ),
        "non_indexable_section_count": sum(
            not section["indexable"]
            for section in sections
        ),
        "sections_with_code_count": sum(
            section["contains_code"]
            for section in sections
        ),
        "short_section_count": sum(
            "short-section"
            in section["quality_flags"]
            for section in sections
        ),
        "fallback_anchor_count": sum(
            "fallback-heading-anchor"
            in section["quality_flags"]
            for section in sections
        ),
        "low_confidence_anchor_count": sum(
            "low-anchor-confidence"
            in section["quality_flags"]
            for section in sections
        ),
        "warnings": warnings,
    }


def process_document(
    document_config: dict[str, Any],
    minimum_section_characters: int,
) -> None:
    document_id = document_config["id"]

    extracted_directory = (
        EXTRACTED_ROOT / document_id
    )

    document_path = (
        extracted_directory / "document.json"
    )

    pages_path = (
        extracted_directory / "pages.jsonl"
    )

    toc_path = extracted_directory / "toc.json"

    if not document_path.exists():
        raise FileNotFoundError(document_path)

    if not pages_path.exists():
        raise FileNotFoundError(pages_path)

    document_record = load_json(document_path)
    pages = load_jsonl(pages_path)

    toc = (
        load_json(toc_path)
        if toc_path.exists()
        else []
    )

    content_start_page = int(
        document_config.get(
            "content_start_page",
            1,
        )
    )

    configured_end_page = document_config.get(
        "content_end_page"
    )

    content_end_page = (
        int(configured_end_page)
        if configured_end_page is not None
        else None
    )

    units, pages_by_number = flatten_pages(
        pages=pages,
        content_start_page=content_start_page,
        content_end_page=content_end_page,
    )

    if not units:
        raise ValueError(
            f"No text units found for {document_id}"
        )

    body_font_size = detect_body_font_size(units)

    requested_mode = document_config.get(
        "section_detection",
        "auto",
    )

    if requested_mode == "toc":
        detection_mode = "toc"
    elif requested_mode == "font":
        detection_mode = "font"
    elif toc:
        detection_mode = "toc"
    else:
        detection_mode = "font"

    if detection_mode == "toc":
        events, warnings = build_toc_events(
            toc=toc,
            units=units,
            body_font_size=body_font_size,
        )
    else:
        events, warnings = build_font_events(
            document_config=document_config,
            units=units,
            body_font_size=body_font_size,
        )

    sections = build_sections_from_events(
        document_record=document_record,
        events=events,
        units=units,
        pages_by_number=pages_by_number,
        minimum_section_characters=(
            minimum_section_characters
        ),
    )

    output_directory = (
        PROCESSED_ROOT / document_id
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_jsonl(
        output_directory / "sections.jsonl",
        sections,
    )

    report = build_section_report(
        document_id=document_id,
        detection_mode=detection_mode,
        body_font_size=body_font_size,
        sections=sections,
        event_count=len(events),
        warnings=warnings,
    )

    write_json(
        output_directory / "section-report.json",
        report,
    )

    print(
        f"[OK] {document_id}: "
        f"{len(sections)} sections, "
        f"{report['indexable_section_count']} indexable, "
        f"mode={detection_mode}"
    )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build semantically structured sections "
            "from extracted PDF pages."
        )
    )

    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
    )

    parser.add_argument(
        "--document",
        action="append",
        dest="document_ids",
        help=(
            "Process only this document ID. "
            "Can be supplied more than once."
        ),
    )

    parser.add_argument(
        "--minimum-section-characters",
        type=int,
        default=80,
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
                minimum_section_characters=(
                    arguments
                    .minimum_section_characters
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
            "Section construction failed for: "
            + ", ".join(failures)
        )

    print(
        f"Section construction completed for "
        f"{len(documents)} document(s)."
    )


if __name__ == "__main__":
    main()