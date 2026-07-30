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

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DEFAULT_MANIFEST_PATH = (
    PROJECT_ROOT
    / "data"
    / "manifests"
    / "documents.yaml"
)

EXTRACTED_ROOT = PROJECT_ROOT / "data" / "extracted"
PROCESSED_ROOT = PROJECT_ROOT / "data" / "processed"


TOKEN_PATTERN = re.compile(
   r"\w+|[^\w\s]"
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


@dataclass(@frozen=True)
class TextAtom:
   text: str
   page_number: int
   source_block_id: str
   likely_code_block: bool

   # convert this token_count() function to variable like token_count
   @property
   def token_count(self) -> int: 
      return approximate_token_count(self.text)

def approximate_token_count(text: str) -> int:
   return len(TOKEN_PATTERN.findall(text))


def normalize_for_hash(text: str) -> str :
   return re.sub(
      r"\s+",
      " ",
      text.casefold()
   ).strip()

def calculate_text_hash(text : str) -> str:
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
    """
    input ->
    pages = [
    {
        "page_number": "1",
        "blocks": [
            {
                # Header repeated on every page
                "is_repeated_margin": True,
                "text": "COMPANY CONFIDENTIAL",
                "block_index": 0,
            },
            {
                # Valid text block
                "text": "  def hello_world():\n      print('Hello')  ",
                "block_index": 1,
                "likely_code_block": True,
            },
            {
                # Empty block
                "text": "   ",
                "block_index": 2,
            },
        ],
    }
]


   -> output 
   {
    "page-0001/block-001": {
        "source_block_id": "page-0001/block-001",
        "page_number": 1,
        "block_index": 1,
        "text": "def hello_world():\n      print('Hello')",  # Cleaned & stripped
        "likely_code_block": True,
    }
}
    """
    
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




