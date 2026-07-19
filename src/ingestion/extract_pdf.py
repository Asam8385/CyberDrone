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

PROJECT_ROOT = Path(__file__).resolve().parent[2]

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







