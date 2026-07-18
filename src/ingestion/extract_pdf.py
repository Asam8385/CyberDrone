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
