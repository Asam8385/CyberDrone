from __future__ import annotations # reduce the errors

import argparse
import hashlib
import json
import math
import re
from collections import defaultdict
from datetime import datetime , timezone
from pathlib import Path
from typing import Any

import pymupdf
import yaml

SCHEMA_VERSION = "1.0"

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DEFAULT_MANIFEST_PATH = (
   PROJECT_ROOT / "data" / "manifests" / "documents.yaml"
)

EXTRACTED_ROOT = PROJECT_ROOT / "data" / "extracted"



REQUIRED_DOCUMENT_FIELDS = {
    "id",
    "path",
    "title",
    "publication_year",
    "document_type",
    "domain",
    "chunk_profile",
}


COMMAND_PREFIXES = (
    # Shell prompts
    "$ ",
    "# ",
    "> ",
    "% ",
    "~$ ",
    "~# ",
    "PS> ",
    "PS C:",
    "C:\\",
    "C:/",
    "sudo ",

    # Scripting / interpreters
    "python ",
    "python3 ",
    "python2 ",
    "pip ",
    "pip3 ",
    "ruby ",
    "perl ",
    "node ",
    "php ",
    "bash ",
    "sh ",
    "zsh ",
    "powershell ",
    "pwsh ",

    # Networking / transfer
    "curl ",
    "wget ",
    "nc ",
    "ncat ",
    "netcat ",
    "ssh ",
    "scp ",
    "sftp ",
    "telnet ",
    "ftp ",
    "ping ",
    "traceroute ",
    "tracert ",
    "dig ",
    "nslookup ",
    "host ",

    # Recon / scanning tools
    "nmap ",
    "masscan ",
    "sqlmap ",
    "nikto ",
    "ffuf ",
    "gobuster ",
    "dirsearch ",
    "wfuzz ",
    "hydra ",
    "john ",
    "hashcat ",
    "metasploit ",
    "msfconsole ",
    "msfvenom ",
    "burpsuite ",
    "wpscan ",
    "amass ",
    "subfinder ",
    "nuclei ",
    "whatweb ",
    "theharvester ",

    # Container / infra tooling
    "docker ",
    "docker-compose ",
    "kubectl ",
    "helm ",
    "terraform ",
    "ansible ",
    "vagrant ",

    # Version control / package managers
    "git ",
    "npm ",
    "yarn ",
    "cargo ",
    "go ",
    "apt ",
    "apt-get ",
    "yum ",
    "dnf ",
    "brew ",
    "choco ",

    # HTTP methods (raw request lines)
    "GET ",
    "POST ",
    "PUT ",
    "PATCH ",
    "DELETE ",
    "OPTIONS ",
    "HEAD ",
    "CONNECT ",
    "TRACE ",
)


COMMAND_PATTERNS = (
    # Generic CLI invocation: `tool --flag` or `tool -f`
    re.compile(r"^\s*(?:sudo\s+)?[a-zA-Z0-9_.-]+\s+--?[a-zA-Z]"),

    # HTTP request lines: METHOD /path [HTTP/1.1]
    re.compile(r"^\s*(?:GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD|CONNECT|TRACE)\s+\S+"),

    # Environment variable assignment: VAR=value or export VAR=value
    re.compile(r"^\s*(?:export\s+)?[A-Z_][A-Z0-9_]*="),

    # SQL statements
    re.compile(
        r"^\s*(?:SELECT|INSERT|UPDATE|DELETE|UNION|CREATE|DROP|ALTER|GRANT|EXEC)\s+",
        re.I,
    ),

    # Shell prompt markers at start of line
    re.compile(r"^\s*(?:\$|#|>|%)\s+\S"),
    re.compile(r"^\s*PS(?:\s+[A-Z]:\\[^>]*)?>\s*\S"),

    # Piped / chained commands
    re.compile(r"^\s*[a-zA-Z0-9_./-]+\s*\|\s*[a-zA-Z0-9_./-]+"),

    # Redirection operators
    re.compile(r"^\s*[a-zA-Z0-9_./-]+.*(?:>>|>|<)\s*\S+"),

    # URL / endpoint patterns (bare, without HTTP verb)
    re.compile(r"^\s*(?:https?://|ftp://|ws://|wss://)\S+"),

    # File paths as standalone lines (Unix and Windows)
    re.compile(r"^\s*(?:/[a-zA-Z0-9_.-]+){2,}/?\s*$"),
    re.compile(r"^\s*[A-Za-z]:\\(?:[^\\/:*?\"<>|\r\n]+\\)*[^\\/:*?\"<>|\r\n]*\s*$"),

    # JSON-like key-value config lines: "key": "value" or key: value
    re.compile(r'^\s*"[a-zA-Z0-9_.-]+"\s*:\s*\S'),

    # Regex/CIDR/IP-looking tokens on their own line (common in networking docs)
    re.compile(r"^\s*(?:\d{1,3}\.){3}\d{1,3}(?:/\d{1,2})?\s*$"),

    # Package manager install commands
    re.compile(
        r"^\s*(?:pip3?|npm|yarn|cargo|go|apt(?:-get)?|yum|dnf|brew|choco|gem)\s+"
        r"(?:install|add|get|update)\s+\S+"
    ),

    # Docker/Kubernetes resource commands
    re.compile(r"^\s*(?:docker|kubectl|helm)\s+[a-z]+\s+\S+"),

    # Git commands
    re.compile(r"^\s*git\s+(?:clone|commit|push|pull|checkout|merge|rebase|log)\b"),

    # Flags/options block (common in "command reference" tables), e.g. `-v, --verbose`
    re.compile(r"^\s*-[a-zA-Z](?:,\s*--[a-zA-Z-]+)?\s"),

    # Function/command call syntax: `funcname(args)`
    re.compile(r"^\s*[a-zA-Z_][a-zA-Z0-9_]*\([^)]*\)\s*$"),
)


def utc_now() -> None:
   """
   this function return global time. to remove the time confict
   we used the timezone.utc to maintain the global standard
   """
   return datetime.now(timezone.utc).isoformat() 



def calculate_sha256(path : Path) -> str :
   """
   Calculating a SHA-256 hash (Secure Hash Algorithm 256-bit) 
   acts as a unique digital fingerprint for your PDF file.

   No matter how large the book is, the hash takes that entire 
   file and condenses it into a single, fixed-size string of 64 
   characters, like this:
   e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca
   495991b7852b855
   
   In a document processing and RAG pipeline, you calculate this 
   hash for three main reasons:
   
   1. To Skip Redundant Work (Caching)
   Extracting text, running OCR, parsing tables, and 
   chunking sections from a massive 500-page pentesting 
   manual takes time and computing power.
   
   Before running the heavy extraction code, the script 
   can check: "Does the current file's SHA match the SHA 
   from the last time we ran this?"
   
   If yes: The file hasn't changed. Skip it entirely and 
   save time.
   
   If no: The file was updated. Re-extract it.
   
   2. File Change Detection (Tamper Evident)
   If someone modifies even a single character, drops an extra 
   space, or updates a command payload inside that PDF, 
   the SHA-256 fingerprint will change completely. 
   This is called the avalanche effect.
   
   By tracking the hash, your system instantly knows if a source file was altered, broken, or replaced with a newer edition.
   
   3. Duplicate Prevention
   If you accidentally rename a book from 
   penetration-testing.pdf to pentest_manual_v2.pdf 
   but the internal content is exactly the same, 
   checking the filename won't save you.
   
   However, both files will yield the exact same 
   SHA-256 hash. Your pipeline can catch this instantly, 
   preventing you from uploading duplicate chunks into 
   your AI vector database and wasting money
    """
   
   digest = hashlib.sha256()

   with path.open('rb') as file:
      for block in iter(lambda: file.read(1024 * 1024), b""): # in here file.read() automatically move the pointer , only iter call function until the sentinental value reach
         digest.update(block)
   
   return digest.hexdigest()


def clean_text_value(text: str) -> str:
   """
    Perform only safe normalization.

    Do not join hyphenated lines or collapse all whitespace here.
    Those operations can damage commands and HTTP requests.
    """
   return (
        text.replace("\x00", "")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )


def bbox_to_list(value: Any) -> list[float]:
    """
    Safely normalizes and rounds bounding box coordinates from a PDF parser.

    Why this is used:
    -----------------
    PDF parsing engines frequently extract raw coordinate text in messy, non-uniform 
    formats (e.g., highly precise strings like ["45.1234567", "102.9876543"]). This 
    function is implemented to intercept that raw layout data and transform it into 
    a standardized, database-ready format before storage.

    Benefits:
    ---------
    1. Pipeline Resilience: Acts as a safety gate. By catching 'TypeError' and 
       'ValueError' internally, it prevents corrupt text layout records from 
       crashing entire multi-hour document extraction loops.
    2. Database Memory Savings: Truncating long float fractions down to 3 decimal 
       places significantly cuts down on structural data storage overhead across 
       millions of document token chunks.
    3. UI Layout Consistency: Guarantees that downstream rendering engines (like 
       frontend PDF highlighting viewers) receive a predictable list of float primitives, 
       eliminating runtime casting operations.

    Args:
        value (Any): Raw bounding box coordinates from the PDF engine. Expected 
            to be an iterable sequence of four elements: [x_min, y_min, x_max, y_max].

    Returns:
        list[float]: A clean list of floats rounded to 3 decimal places. Returns 
            an empty list `[]` if input data is falsy, missing, or unparseable.
    """

    if not value:
       return []
    
    try:
       return [round(float(item) , 3) for item in value]
    except (TypeError , ValueError):
       return []
    

def calculate_area(bbox: Any) -> float:
   """
   This function calculates the mathematical area 
   (the total physical space covered) of a bounding box on a 
   PDF page.

   It acts as a utility to measure how large a specific 
   paragraph, code block, or image container is.
   """
   try:
      return max(0.0 , pymupdf.Rect(bbox).get_area())
   except (TypeError , ValueError):
      return 0.0


def load_manifest(path : Path) -> list[dict[str, Any]]:
   if not path.exists():
      raise FileNotFoundError(f"Manifest not found: {path}")
   
   with path.open("r" , encoding="utf-8") as file:
      manifest = yaml.safe_load(file) or {}

   documents = manifest.get("documents")

   if not isinstance(documents, list) or not documents:
      raise ValueError(
         "The manifest must contain a non-empty 'documents' list."
      )
   
   seen_ids : set[str] = set()

   for index , document in enumerate(documents):
      if not isinstance(document , dict):
         raise(
            f"Document entry {index} must be a YAML mapping."
         )
      
      missing = REQUIRED_DOCUMENT_FIELDS - document.keys()


      if missing:
         raise ValueError(
                   f"Document entry {index} is missing: "
                   f"{', '.join(sorted(missing))}"
               )

      document_id = str(document["id"])

      if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", document_id):
            raise ValueError(
                f"Invalid document ID '{document_id}'. "
                "Use lowercase letters, numbers and hyphens."
            )
      
      if document_id in seen_ids:
            raise ValueError(
                f"Duplicate document ID: {document_id}"
            )
      
      seen_ids.add(document_id)

   return documents

def  write_json(path : Path , value : Any) -> None:
   path.parent.mkdir(parents=True ,  exist_ok=True)
   temporary_path = path.with_name(path.name + ".tmp")

   with temporary_path.open("w" , encoding="utf-8") as file:
      json.dump(
         value,
         file ,
         ensure_ascii=False , 
         indent=2
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


def look_like_command(text: str) -> bool:
   stripped = text.lstrip()

   if stripped.startswith(COMMAND_PREFIXES):
      return True

   return any(
      pattern.search(text) for pattern in COMMAND_PATTERNS
   )

def extract_span(span : dict[str, Any]) -> dict[str , Any] :
   flags = int(span.get("flags" , 0))
   text = clean_text_value(str(span.get("text" , 0)))

   return {
      "text" : text , 
      "bbox" : bbox_to_list(span.get("bbox")),
      "origin": bbox_to_list(span.get("origin")),
      "font": span.get("font"),
      "font_size": round(
                  float(span.get("size", 0.0)),
                  3,
      ),
      "flags": flags,
              "is_bold": bool(
                  flags & pymupdf.TEXT_FONT_BOLD
              ),
              "is_italic": bool(
                  flags & pymupdf.TEXT_FONT_ITALIC
              ),
              "is_monospaced": bool(
                  flags & pymupdf.TEXT_FONT_MONOSPACED
              ),
              "is_superscript": bool(
                  flags & pymupdf.TEXT_FONT_SUPERSCRIPT
              ),
              "color": span.get("color"),


   }


def extract_line(line: dict[dict[str, Any]]) -> dict[str, Any] | None:
   spans = [
      extract_span(span)
      for span in line.get("spans", [])
      if str(span.get("text", ""))
   ]

   if not spans:
      return None

   text = "".join(
           span["text"] for span in spans
       )

   total_characters = sum(
           len(span["text"]) for span in spans
       )

   monospaced_characters = sum(
           len(span["text"])
           for span in spans
           if span["is_monospaced"]
       )

   monospaced_ratio = (
           monospaced_characters / total_characters
           if total_characters
           else 0.0
       )

   return {
           "text": text,
           "bbox": bbox_to_list(line.get("bbox")),
           "direction": bbox_to_list(
               line.get("dir", (1.0, 0.0))
           ),
           "writing_mode": line.get("wmode", 0),
           "spans": spans,
           "monospaced_ratio": round(
               monospaced_ratio,
               4,
           ),
           "contains_command_pattern": look_like_command(text),
       }




def classify_code_block(
    lines: list[dict[str, Any]],
) -> tuple[bool, float]:
    if not lines:
        return False, 0.0

    total_characters = 0
    monospaced_characters = 0
    command_lines = 0

    for line in lines:
        line_length = len(line["text"])
        total_characters += line_length

        monospaced_characters += int(
            line_length * line["monospaced_ratio"]
        )

        if line["contains_command_pattern"]:
            command_lines += 1

    monospaced_ratio = (
        monospaced_characters / total_characters
        if total_characters
        else 0.0
    )

    command_ratio = command_lines / len(lines)

    likely_code = (
        monospaced_ratio >= 0.55
        or command_ratio >= 0.40
        or (
            monospaced_ratio >= 0.30
            and command_lines > 0
        )
    )

    confidence = max(
        monospaced_ratio,
        command_ratio,
    )

    return likely_code, round(confidence, 4)


def extract_text_blocks(
      page: pymupdf.Page,
) -> list[dict[str , Any]] :
   """
       Extract text structure without including image byte data.
   
       TEXTFLAGS_TEXT prevents binary images from being embedded
       inside the returned dictionary.
   """

   page_dictionary = page.get_text(
      "dict", 
      sort = True , 
      flags=pymupdf.TEXTFLAGS_TEXT , 

   )

   results : list[dict[str , Any]] = []

   for original_block_index, block in enumerate(
        page_dictionary.get("blocks", [])
    ):
        if block.get("type") != 0:
            continue

        lines: list[dict[str, Any]] = []

        for line in block.get("lines", []):
            extracted_line = extract_line(line)

            if extracted_line is not None:
                lines.append(extracted_line)

        if not lines:
            continue

        block_text = "\n".join(
            line["text"] for line in lines
        )

        likely_code, code_confidence = classify_code_block(lines)

        results.append(
            {
                "block_index": len(results),
                "source_block_index": original_block_index,
                "bbox": bbox_to_list(block.get("bbox")),
                "text": block_text,
                "lines": lines,
                "likely_code_block": likely_code,
                "code_confidence": code_confidence,
                "is_repeated_margin": False,
            }
        )

   return results


def extract_image_metadata(
    page: pymupdf.Page,
    document_id: str,
) -> list[dict[str, Any]]:
    """
    Record image placement information only.

    This does not save images and does not perform OCR.
    """
    page_area = max(page.rect.get_area(), 1.0)
    results: list[dict[str, Any]] = []

    for image_index, image in enumerate(
        page.get_image_info(xrefs=True),
        start=1,
    ):
        bbox = bbox_to_list(image.get("bbox"))
        image_area = calculate_area(bbox)
        digest = image.get("digest")

        if isinstance(digest, bytes):
            digest = digest.hex()

        results.append(
            {
                "image_id": (
                    f"{document_id}/"
                    f"page-{page.number + 1:04d}/"
                    f"image-{image_index:03d}"
                ),
                "document_id": document_id,
                "page_number": page.number + 1,
                "image_index": image_index,
                "xref": image.get("xref"),
                "bbox": bbox,
                "width": image.get("width"),
                "height": image.get("height"),
                "bits_per_component": image.get("bpc"),
                "colorspace": image.get("colorspace"),
                "colorspace_name": image.get("cs-name"),
                "x_resolution": image.get("xres"),
                "y_resolution": image.get("yres"),
                "digest": digest,
                "page_coverage_ratio": round(
                    image_area / page_area,
                    4,
                ),
            }
        )

    return results


def extract_tables(
    page: pymupdf.Page,
    document_id: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    results: list[dict[str, Any]] = []
    errors: list[str] = []

    try:
        detected = page.find_tables()
    except Exception as error:
        return [], [
            f"Table detection failed on page "
            f"{page.number + 1}: {error}"
        ]

    for table_index, table in enumerate(
        detected.tables,
        start=1,
    ):
        try:
            cells = table.extract()
        except Exception as error:
            cells = []
            errors.append(
                f"Table cell extraction failed on page "
                f"{page.number + 1}, table {table_index}: {error}"
            )

        try:
            markdown = table.to_markdown()
        except Exception as error:
            markdown = None
            errors.append(
                f"Table Markdown conversion failed on page "
                f"{page.number + 1}, table {table_index}: {error}"
            )

        row_count = len(cells)
        column_count = max(
            (
                len(row)
                for row in cells
                if isinstance(row, list)
            ),
            default=0,
        )

        results.append(
            {
                "table_id": (
                    f"{document_id}/"
                    f"page-{page.number + 1:04d}/"
                    f"table-{table_index:03d}"
                ),
                "document_id": document_id,
                "page_number": page.number + 1,
                "table_index": table_index,
                "bbox": bbox_to_list(table.bbox),
                "row_count": row_count,
                "column_count": column_count,
                "cells": cells,
                "markdown": markdown,
            }
        )

    return results, errors


def extract_toc(
    document: pymupdf.Document,
) -> list[dict[str, Any]]:
    raw_toc = document.get_toc(simple=True)
    results: list[dict[str, Any]] = []
    parent_stack: dict[int, str] = {}

    for index, item in enumerate(raw_toc, start=1):
        level, title, page_number = item
        toc_id = f"toc-{index:04d}"

        parent_id = (
            parent_stack.get(level - 1)
            if level > 1
            else None
        )

        results.append(
            {
                "toc_id": toc_id,
                "parent_toc_id": parent_id,
                "level": level,
                "title": clean_text_value(title).strip(),
                "page_number": page_number,
            }
        )

        parent_stack[level] = toc_id

        for existing_level in list(parent_stack):
            if existing_level > level:
                del parent_stack[existing_level]

    return results


def normalize_margin_signature(text: str) -> str:
    """
    Normalize changing page numbers so repeated headers and footers
    can still be identified.
    """
    value = text.casefold().strip()
    value = re.sub(r"\b\d+\b", "<number>", value)
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"[^\w<>:/|&.-]+", " ", value)
    return value.strip()


def get_margin_signature(
    block: dict[str, Any],
    page_height: float,
) -> str | None:
    bbox = block.get("bbox", [])

    if len(bbox) != 4 or page_height <= 0:
        return None

    _, y0, _, y1 = bbox

    if y1 <= page_height * 0.12:
        region = "top"
    elif y0 >= page_height * 0.88:
        region = "bottom"
    else:
        return None

    text = block.get("text", "").strip()

    if not text or len(text) > 180:
        return None

    signature = normalize_margin_signature(text)

    if not signature:
        return None

    return f"{region}:{signature}"


def find_repeated_margin_signatures(
    page_records: list[dict[str, Any]],
) -> set[str]:
    signature_pages: dict[str, set[int]] = defaultdict(set)

    for page in page_records:
        page_number = page["page_number"]
        page_height = page["height"]

        for block in page.get("blocks", []):
            signature = get_margin_signature(
                block,
                page_height,
            )

            if signature:
                signature_pages[signature].add(page_number)

    page_count = len(page_records)

    minimum_occurrences = max(
        4,
        min(
            12,
            math.ceil(page_count * 0.05),
        ),
    )

    return {
        signature
        for signature, pages in signature_pages.items()
        if len(pages) >= minimum_occurrences
    }


def remove_repeated_margins(
    page_records: list[dict[str, Any]],
) -> set[str]:
    repeated_signatures = find_repeated_margin_signatures(
        page_records
    )

    for page in page_records:
        retained_text: list[str] = []
        removed_text: list[str] = []

        for block in page.get("blocks", []):
            signature = get_margin_signature(
                block,
                page["height"],
            )

            is_repeated = (
                signature in repeated_signatures
                if signature
                else False
            )

            block["is_repeated_margin"] = is_repeated

            if is_repeated:
                removed_text.append(block["text"])
            else:
                retained_text.append(block["text"])

        page["text"] = "\n\n".join(retained_text).strip()
        page["removed_margin_text"] = removed_text
        page["character_count"] = len(page["text"])
        page["word_count"] = len(page["text"].split())
        page["has_native_text"] = bool(page["text"])

    return repeated_signatures


def extract_page(
    page: pymupdf.Page,
    document_id: str,
    enable_tables: bool,
) -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[str],
]:
    blocks = extract_text_blocks(page)
    initial_text = "\n\n".join(
        block["text"] for block in blocks
    ).strip()

    images = extract_image_metadata(
        page=page,
        document_id=document_id,
    )

    table_records: list[dict[str, Any]] = []
    table_errors: list[str] = []

    if enable_tables:
        table_records, table_errors = extract_tables(
            page=page,
            document_id=document_id,
        )

    max_image_coverage = max(
        (
            image["page_coverage_ratio"]
            for image in images
        ),
        default=0.0,
    )

    page_record = {
        "document_id": document_id,
        "page_number": page.number + 1,
        "width": round(page.rect.width, 3),
        "height": round(page.rect.height, 3),
        "rotation": page.rotation,
        "text": initial_text,
        "character_count": len(initial_text),
        "word_count": len(initial_text.split()),
        "has_native_text": bool(initial_text),
        "extraction_method": "native",
        "blocks": blocks,
        "image_ids": [
            image["image_id"] for image in images
        ],
        "image_count": len(images),
        "max_image_coverage_ratio": max_image_coverage,
        "table_ids": [
            table["table_id"] for table in table_records
        ],
        "table_count": len(table_records),
        "removed_margin_text": [],
    }

    return (
        page_record,
        images,
        table_records,
        table_errors,
    )


def build_extraction_report(
    document_id: str,
    page_records: list[dict[str, Any]],
    toc: list[dict[str, Any]],
    image_records: list[dict[str, Any]],
    table_records: list[dict[str, Any]],
    repeated_margin_signatures: set[str],
    warnings: list[str],
) -> dict[str, Any]:
    empty_pages = [
        page["page_number"]
        for page in page_records
        if page["character_count"] == 0
    ]

    low_text_pages = [
        page["page_number"]
        for page in page_records
        if 0 < page["character_count"] < 80
    ]

    image_only_candidates = [
        page["page_number"]
        for page in page_records
        if (
            page["character_count"] < 50
            and page["max_image_coverage_ratio"] >= 0.60
        )
    ]

    pages_with_code = [
        page["page_number"]
        for page in page_records
        if any(
            block["likely_code_block"]
            for block in page["blocks"]
        )
    ]

    pages_with_tables = [
        page["page_number"]
        for page in page_records
        if page["table_count"] > 0
    ]

    pages_with_images = [
        page["page_number"]
        for page in page_records
        if page["image_count"] > 0
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "document_id": document_id,
        "generated_at": utc_now(),
        "page_count": len(page_records),
        "toc_entry_count": len(toc),
        "total_character_count": sum(
            page["character_count"]
            for page in page_records
        ),
        "empty_page_count": len(empty_pages),
        "empty_pages": empty_pages,
        "low_text_page_count": len(low_text_pages),
        "low_text_pages": low_text_pages,
        "image_metadata_count": len(image_records),
        "pages_with_images": pages_with_images,
        "image_only_candidate_pages": image_only_candidates,
        "table_count": len(table_records),
        "pages_with_tables": pages_with_tables,
        "pages_with_code_blocks": pages_with_code,
        "repeated_margin_signature_count": len(
            repeated_margin_signatures
        ),
        "warnings": warnings,
        "ocr_used": False,
    }


def extract_document(
    document_config: dict[str, Any],
    skip_tables: bool,
) -> None:
    document_id = document_config["id"]
    source_path = (
        PROJECT_ROOT / document_config["path"]
    ).resolve()

    if not source_path.exists():
        raise FileNotFoundError(
            f"PDF not found for '{document_id}': {source_path}"
        )

    if source_path.suffix.casefold() != ".pdf":
        raise ValueError(
            f"Source is not a PDF: {source_path}"
        )

    output_directory = EXTRACTED_ROOT / document_id
    output_directory.mkdir(parents=True, exist_ok=True)

    enable_tables = (
        bool(document_config.get("extract_tables", True))
        and not skip_tables
    )

    page_records: list[dict[str, Any]] = []
    image_records: list[dict[str, Any]] = []
    table_records: list[dict[str, Any]] = []
    warnings: list[str] = []

    document = pymupdf.open(source_path)

    try:
        toc = extract_toc(document)

        for page in document:
            try:
                (
                    page_record,
                    page_images,
                    page_tables,
                    page_warnings,
                ) = extract_page(
                    page=page,
                    document_id=document_id,
                    enable_tables=enable_tables,
                )

                page_records.append(page_record)
                image_records.extend(page_images)
                table_records.extend(page_tables)
                warnings.extend(page_warnings)

            except Exception as error:
                page_number = page.number + 1

                warnings.append(
                    f"Page extraction failed on page "
                    f"{page_number}: {error}"
                )

                page_records.append(
                    {
                        "document_id": document_id,
                        "page_number": page_number,
                        "width": round(page.rect.width, 3),
                        "height": round(page.rect.height, 3),
                        "rotation": page.rotation,
                        "text": "",
                        "character_count": 0,
                        "word_count": 0,
                        "has_native_text": False,
                        "extraction_method": "failed",
                        "blocks": [],
                        "image_ids": [],
                        "image_count": 0,
                        "max_image_coverage_ratio": 0.0,
                        "table_ids": [],
                        "table_count": 0,
                        "removed_margin_text": [],
                        "extraction_error": str(error),
                    }
                )

        repeated_margin_signatures = remove_repeated_margins(
            page_records
        )

        source_hash = calculate_sha256(source_path)

        document_record = {
            "schema_version": SCHEMA_VERSION,
            "document_id": document_id,
            "source_path": document_config["path"],
            "source_filename": source_path.name,
            "source_sha256": source_hash,
            "title": document_config["title"],
            "author": document_config.get("author"),
            "publication_year": document_config[
                "publication_year"
            ],
            "document_type": document_config[
                "document_type"
            ],
            "domain": document_config["domain"],
            "chunk_profile": document_config[
                "chunk_profile"
            ],
            "freshness_warning": document_config.get(
                "freshness_warning",
                False,
            ),
            "language": document_config.get(
                "language",
                "en",
            ),
            "trust_tier": document_config.get(
                "trust_tier",
                3,
            ),
            "page_count": len(document),
            "toc_entry_count": len(toc),
            "table_extraction_enabled": enable_tables,
            "ocr_enabled": False,
            "extractor": "pymupdf",
            "extractor_version": pymupdf.VersionBind,
            "extracted_at": utc_now(),
        }

        extraction_report = build_extraction_report(
            document_id=document_id,
            page_records=page_records,
            toc=toc,
            image_records=image_records,
            table_records=table_records,
            repeated_margin_signatures=(
                repeated_margin_signatures
            ),
            warnings=warnings,
        )

        write_json(
            output_directory / "document.json",
            document_record,
        )

        write_json(
            output_directory / "toc.json",
            toc,
        )

        write_jsonl(
            output_directory / "pages.jsonl",
            page_records,
        )

        write_jsonl(
            output_directory / "tables.jsonl",
            table_records,
        )

        write_jsonl(
            output_directory / "images.jsonl",
            image_records,
        )

        write_json(
            output_directory / "extraction-report.json",
            extraction_report,
        )

        print(
            f"[OK] {document_id}: "
            f"{len(page_records)} pages, "
            f"{len(toc)} TOC entries, "
            f"{len(table_records)} tables, "
            f"{len(warnings)} warnings"
        )

    finally:
        document.close()


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract structured native text, tables, "
            "bookmarks and image metadata from PDFs."
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
            "Extract only the specified document ID. "
            "Can be supplied multiple times."
        ),
    )

    parser.add_argument(
        "--skip-tables",
        action="store_true",
        help="Disable table detection.",
    )

    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()

    manifest_path = arguments.manifest

    if not manifest_path.is_absolute():
        manifest_path = PROJECT_ROOT / manifest_path

    documents = load_manifest(
        manifest_path.resolve()
    )

    selected_ids = set(arguments.document_ids or [])

    if selected_ids:
        known_ids = {
            document["id"] for document in documents
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

    EXTRACTED_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    failed_documents: list[str] = []

    for document in documents:
        try:
            extract_document(
                document_config=document,
                skip_tables=arguments.skip_tables,
            )
        except Exception as error:
            document_id = document.get("id", "unknown")
            failed_documents.append(document_id)

            print(
                f"[ERROR] {document_id}: {error}"
            )

    if failed_documents:
        raise SystemExit(
            "Extraction failed for: "
            + ", ".join(failed_documents)
        )

    print(
        f"Extraction completed for "
        f"{len(documents)} document(s)."
    )


if __name__ == "__main__":
    main()


   





                           









