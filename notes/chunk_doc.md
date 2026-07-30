# Document Chunking Pipeline — Explained

This script is a **document-chopping machine**. It takes documents that have
already been extracted from PDFs (page by page, block by block) and cuts them
into small, well-sized pieces ("chunks") that can be sent to an embedding
model (like Google's `text-embedding-004` / `gemini-embedding-001`) for
semantic search / RAG (retrieval-augmented generation).

Embedding models can only accept a limited amount of text per request. This
script's whole job is: **split big documents into small, overlapping,
context-labeled pieces — without cutting through the middle of important
content — and keep track of exactly where each piece came from.**

---

## 1. Setup / Configuration (top of file)

### `SCHEMA_VERSION`
A version string (`"1.0"`) stamped onto every output record. If you ever
change the structure of the output records later, you bump this — so
downstream code can tell "old format" records from "new format" ones.

### `PROJECT_ROOT`, `DEFAULT_MANIFEST_PATH`, `EXTRACTED_ROOT`, `PROCESSED_ROOT`
Just folder path constants:
- `PROJECT_ROOT` — the root of the whole project.
- `DEFAULT_MANIFEST_PATH` — where the list of documents to process lives
  (`data/manifests/documents.yaml`).
- `EXTRACTED_ROOT` — where raw PDF-extracted data lives (pages/blocks, before
  chunking).
- `PROCESSED_ROOT` — where the final chunked output goes.

Think of this as: **raw input folder → this script → processed output
folder**.

### `TOKEN_PATTERN`
```python
TOKEN_PATTERN = re.compile(r"\w+|[^\w\s]", flags=re.UNICODE)
```
A regular expression used to *estimate* how many "tokens" (word-ish chunks)
are in a string. It matches either:
- `\w+` → a run of word characters (letters/digits/underscore) — e.g. `"hello"`, `"2023"`
- `[^\w\s]` → a single non-word, non-space character — e.g. `,` `.` `!` `(`

**Example:**
```
"Sales grew 40%, year-over-year!"
→ ["Sales", "grew", "40", "%", "year", "-", "over", "-", "year", "!"]
→ 10 tokens (approximately)
```

⚠️ **Important:** this is *not* the real tokenizer that Google's embedding
model uses internally (which uses SentencePiece / BPE). It's a cheap,
fast, "good enough" stand-in used only to keep chunk sizes roughly under
control during chunking. The code comment even says so:

```python
# This is an approximate, model-independent tokenizer.
# Use the embedding model's real tokenizer during indexing.
```

### `CHUNK_PROFILES`
A dictionary of preset chunking rules per document type:

| Profile | max tokens | overlap tokens | min tokens | Used for |
|---|---|---|---|---|
| `case_study` | 450 | 60 | 60 | Business case studies |
| `technical_book` | 500 | 75 | 70 | Dense technical books |
| `training_book` | 500 | 75 | 70 | Training material |
| `command_reference` | 250 | 30 | 25 | Short command docs |
| `default` | 450 | 60 | 60 | Fallback for anything else |

**Why different sizes per type?** A command reference entry is short and
self-contained (small chunks make sense), while a technical book chapter
needs more surrounding context to make sense on its own (bigger chunks with
more overlap).

---

## 2. `TextAtom` (dataclass)

```python
@dataclass(frozen=True)
class TextAtom:
    text: str
    page_number: int
    source_block_id: str
    likely_code_block: bool
```

An **"atom"** is the smallest unit of text the pipeline works with — usually
one paragraph/block from the PDF. Think of atoms as **LEGO bricks**; chunks
are built by snapping several atoms together.

- `text` — the actual text content.
- `page_number` — which PDF page it came from (for citations).
- `source_block_id` — a unique ID like `"page-0004/block-002"` so you can
  trace this atom back to the original PDF block.
- `likely_code_block` — `True` if this text looks like a code snippet
  (affects formatting/handling decisions downstream).

It also has a computed property:
```python
@property
def token_count(self) -> int:
    return approximate_token_count(self.text)
```
So you can call `atom.token_count` any time without manually re-counting.

`frozen=True` means once created, a `TextAtom` can't be modified — this
avoids accidental bugs where one part of the code changes an atom's text
after another part already counted its tokens.

---

## 3. Token & Text Utilities

### `approximate_token_count(text: str) -> int`
```python
def approximate_token_count(text: str) -> int:
    return len(TOKEN_PATTERN.findall(text))
```
Counts how many regex "tokens" are in a string. Used everywhere a chunk size
needs to be estimated quickly, without calling an actual tokenizer/API.

**Example:**
```python
approximate_token_count("Hello, world!")  # → 4  ("Hello" "," "world" "!")
```

### `normalize_for_hash(text: str) -> str`
```python
def normalize_for_hash(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold()).strip()
```
Cleans text before hashing:
- `casefold()` — lowercases text (more aggressive than `.lower()`, better for
  matching across languages).
- `re.sub(r"\s+", " ", ...)` — collapses multiple spaces/tabs/newlines into a
  single space.
- `.strip()` — removes leading/trailing whitespace.

**Example:**
```
"  Hello   World  \n"  →  "hello world"
```

### `calculate_text_hash(text: str) -> str`
```python
def calculate_text_hash(text: str) -> str:
    normalized = normalize_for_hash(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
```
Produces a fingerprint (SHA-256 hash) of the *normalized* text.

**Why:** to detect duplicate content. Two blocks that differ only in
capitalization or spacing will normalize to the same string and thus produce
the **same hash** — letting the pipeline recognize them as duplicates (e.g.
a repeated boilerplate paragraph, or a header that shows up on every page).

**Example:**
```python
calculate_text_hash("Hello   World")   # → abc123...
calculate_text_hash("hello world")     # → abc123...  (same hash!)
```

---

## 4. File I/O Helpers

### `load_json(path: Path) -> Any`
Opens a `.json` file and parses it into a Python object. Simple wrapper
around `json.load`.

### `load_jsonl(path: Path) -> list[dict[str, Any]]`
Reads a `.jsonl` file (JSON Lines — **one JSON object per line**, common for
large datasets since you can stream/process line-by-line instead of loading
one giant array). It:
- Skips blank lines.
- Parses each line as JSON.
- If a line fails to parse, raises a clear error telling you **which file and
  line number** broke — much easier to debug than a generic JSON error.

**Example file (`chunks.jsonl`):**
```
{"id": 1, "text": "..."}
{"id": 2, "text": "..."}
```

### `write_json(path: Path, value: Any) -> None`
Writes a Python object to a `.json` file, safely:
1. Creates parent directories if they don't exist.
2. Writes to a **temporary file** first (`file.json.tmp`).
3. Renames the temp file to the real filename only after the write finishes.

**Why the temp-file trick?** If the program crashes or is killed mid-write,
you'd normally end up with a half-written, corrupted JSON file. By writing to
a `.tmp` file and renaming it at the end (an atomic operation on most
filesystems), the real file either has the *old* complete content or the
*new* complete content — never something broken in between.

### `write_jsonl(path: Path, records: list[dict]) -> None`
Same safety pattern as `write_json`, but writes one JSON object per line
(compact, no extra whitespace via `separators=(",", ":")`), matching the
JSONL format used by `load_jsonl`.

---

## 5. Manifest Loading

### `load_manifest(path: Path) -> list[dict[str, Any]]`
Reads the `documents.yaml` file — the **"recipe list"** that tells the
pipeline which documents exist and how to process each one.

```python
if not path.exists():
    raise FileNotFoundError(...)
...
documents = manifest.get("documents", [])
if not isinstance(documents, list) or not documents:
    raise ValueError(...)
```

It fails loudly and clearly if the manifest is missing or malformed (empty,
not a list, etc.) rather than silently processing zero documents.

**Example `documents.yaml`:**
```yaml
documents:
  - document_id: acme-case-study
    title: "Acme Turnaround Case Study"
    document_type: case_study
    chunk_profile: case_study
    source_filename: acme.pdf
  - document_id: python-cookbook
    title: "Python Cookbook"
    document_type: technical_book
    chunk_profile: technical_book
```

---

## 6. Building a Lookup Table for PDF Blocks

### `build_source_block_lookup(pages: list[dict]) -> dict[str, dict]`
Takes the raw extracted PDF structure — a list of pages, each containing a
list of text "blocks" (paragraphs, headers, etc.) — and flattens it into a
**dictionary you can search by ID**.

Step by step:
1. Loop over every page.
2. Loop over every block on that page.
3. **Skip blocks marked `is_repeated_margin`** — these are running
   headers/footers that appear on every page (not real content, so they'd
   just create noise/duplication if included).
4. Skip blocks with empty text.
5. Build an ID like `"page-0004/block-002"`.
6. Store the block's text, page number, block index, and whether it's
   probably code, keyed by that ID.

**Why:** Later steps need to grab a block's text quickly just by knowing its
ID (sections reference blocks by ID, not by full content). This turns a
nested page → block structure into a flat "ID → content" map, like an
address book.

**Example:**
```python
lookup["page-0004/block-002"]
# → {
#     "source_block_id": "page-0004/block-002",
#     "page_number": 4,
#     "block_index": 2,
#     "text": "Revenue grew 40% in Q3.",
#     "likely_code_block": False,
#   }
```

---

## 7. Deciding Chunk Sizes Per Document

### `get_chunk_profile(document_config, maximum_tokens_override, overlap_tokens_override) -> dict[str, int]`
Figures out the **final** chunking rules (`maximum_tokens`, `overlap_tokens`,
`minimum_tokens`) for one document, by layering settings from most-general to
most-specific:

1. **Start with a named profile** (e.g. `"case_study"`) from
   `CHUNK_PROFILES`, falling back to `"default"` if the document doesn't
   specify one or specifies an unknown name.
2. **Apply manifest overrides** — if `documents.yaml` has a `chunking:`
   block for this document with custom values, those override the profile
   defaults.
3. **Apply command-line overrides** — if the user ran the script with
   `--maximum-tokens` or `--overlap-tokens` flags, those win over everything
   else.
4. **Validate** the final numbers:
   - `maximum_tokens` must be > 0.
   - `minimum_tokens` can't be negative.
   - `overlap_tokens` can't be negative.
   - `overlap_tokens` must be **smaller** than `maximum_tokens` (otherwise
     you'd overlap more than a whole chunk, which makes no sense).

**Example — manifest override:**
```yaml
- title: "Special Doc"
  chunk_profile: default
  chunking:
    maximum_tokens: 300   # overrides the default's 450
```

**Priority order (highest wins):**
```
command-line flag  >  manifest "chunking:" override  >  named profile default
```

---

## 8. Splitting Oversized Text

### `split_text_by_token_budget(text: str, maximum_tokens: int) -> list[str]`
Normally, chunks are built by grouping *whole* blocks together. But
sometimes a **single block is too big on its own** — e.g. one giant table or
a huge code dump that alone exceeds `maximum_tokens`. This function handles
that edge case by slicing one long text into smaller pieces.

How it works:
1. Find every token match's position in the text (`token_matches`).
2. If the whole text already fits under `maximum_tokens`, return it as-is
   (no splitting needed) — this is the common case.
3. Otherwise, walk through in windows of `maximum_tokens` tokens at a time,
   slicing the *original text* (not the token list) between the character
   positions of the first and last token in each window. This preserves
   original spacing/formatting within each piece.
4. Strip and collect non-empty pieces.

**Example:**
```python
split_text_by_token_budget("one two three four five six seven", maximum_tokens=5)
# → ["one two three four five", "six seven"]
```

This function is described in the code as being "only used when one block
alone exceeds the configured maximum" — it's a **safety valve**, not the
main chunking mechanism.

---

## 9. Gathering the Raw Material for a Section

### `build_section_atoms(section, block_lookup, maximum_tokens) -> tuple[list[TextAtom], list[str]]`
A **"section"** is a logical unit of the document — like a chapter or a
heading (e.g. "3.1 Financial Overview"). This function gathers all the small
text pieces (atoms) that belong to that section.

Step by step:
1. The section has a list of `source_block_ids` it's made of (e.g. all the
   paragraph blocks under that heading).
2. For each block ID:
   - Look it up in `block_lookup`.
   - If it's **missing** (e.g. data inconsistency), record it in
     `missing_blocks` and skip it — but don't crash.
   - If found, run its text through `split_text_by_token_budget` in case it's
     oversized, and wrap each resulting piece in a `TextAtom`.
3. **Fallback:** if after all that, `atoms` is still empty (e.g. none of the
   block IDs resolved), fall back to using the section's own raw `text`
   field directly (splitting it if needed too). This is a safety net so a
   section never silently becomes "empty" and gets dropped from the index
   just because of a block-ID mismatch.

**Returns:** the list of atoms, plus a list of any block IDs that
couldn't be found (useful for logging/debugging data quality issues).

**Example:**
```
Section "3.1 Overview" has source_block_ids:
  ["page-0003/block-001", "page-0003/block-002"]

→ atoms = [
    TextAtom(text="Revenue grew 40%...", page=3, id="page-0003/block-001", code=False),
    TextAtom(text="This was driven by...", page=3, id="page-0003/block-002", code=False),
  ]
missing_blocks = []
```

---

## 10. Overlap Selection

### `select_overlap_atoms(atoms: list[TextAtom], overlap_token_budget: int) -> list[TextAtom]`
Given the atoms that just filled up a chunk, this picks the **last few
atoms** (from the end) to carry forward and reuse as the *beginning* of the
**next** chunk.

**Why overlap matters:** If chunk 1 ends mid-thought and chunk 2 starts
immediately after, an embedding model reading chunk 2 alone might miss
context. By repeating a bit of the end of chunk 1 at the start of chunk 2,
each chunk stays more self-contained and search results are more coherent.

How it works:
1. If `overlap_token_budget` is 0 or less, return nothing — no overlap
   wanted.
2. Walk **backwards** through the atoms (from the most recent to the
   oldest).
3. Keep adding atoms to the overlap set as long as doing so doesn't exceed
   the token budget.
4. Stop as soon as adding the next atom would go over budget.
5. Reverse the result back into original (forward) order before returning.

**Example:**
```
atoms in chunk 1 (in order): [A(10 tok), B(15 tok), C(20 tok)]
overlap_token_budget = 25

Walk backwards: 
  C (20) → 20 ≤ 25 → keep. running total = 20
  B (15) → 20+15=35 > 25 → stop

→ overlap_atoms = [C]   (just the last atom, since B would've pushed over budget)
```

---

## 11. The Core Chunking Algorithm

### `chunk_atoms(atoms, maximum_tokens, overlap_tokens) -> list[list[TextAtom]]`
This is the **heart of the whole pipeline** — it walks through a section's
atoms and packs them into a list of chunks (each chunk being a list of
atoms), respecting the token budget and adding overlap between consecutive
chunks.

Step by step, in plain English:
1. If there are no atoms, return an empty list.
2. Start with an empty "current chunk" and a running token count of 0.
3. For each atom, one at a time:
   - **Would adding this atom overflow the current chunk?** (only checked if
     the current chunk already has something in it — you always allow at
     least one atom per chunk, even if that one atom alone is close to the
     limit)
     - If yes → **close off the current chunk** (add it to the results
       list).
     - Figure out which atoms from the just-closed chunk should carry over
       as overlap (`select_overlap_atoms`).
     - **Safety check:** if the overlap atoms *plus* the new atom would
       still be too big, trim overlap atoms from the front (oldest first)
       until it fits. This guarantees no chunk can ever exceed
       `maximum_tokens`, even with overlap included.
     - Start the new "current chunk" from those overlap atoms.
   - Add the current atom to the (possibly just-reset) current chunk, and
     update the running token count.
4. After the loop, if there's a leftover partial chunk, add it to the
   results too (it doesn't get thrown away just because it wasn't "full").

**Example (simplified numbers):**
```
maximum_tokens = 10, overlap_tokens = 3
atoms: A(4 tok), B(4 tok), C(4 tok), D(4 tok)

Step 1: add A → chunk=[A], total=4
Step 2: add B → 4+4=8 ≤ 10 → chunk=[A,B], total=8
Step 3: try C → 8+4=12 > 10 → close chunk 1 = [A, B]
        select overlap for budget=3 → walk backward: B(4) > 3 → can't fit B
                                        → overlap_atoms = [] (nothing fits under 3 tokens)
        new chunk starts empty, then add C → chunk=[C], total=4
Step 4: add D → 4+4=8 ≤ 10 → chunk=[C,D], total=8
End of atoms → close final chunk = [C, D]

Result: chunks = [[A, B], [C, D]]
```

If `overlap_tokens` were bigger (say 5), atom `B` (4 tokens) would fit within
the overlap budget, and chunk 2 would start as `[B, C, ...]` instead —
giving the next chunk a bit of shared context with the previous one.

---

## 12. Turning Atoms Back Into Text

### `combine_atom_text(atoms: list[TextAtom]) -> str`
Joins a list of atoms back into one string, with a blank line between each
piece (so paragraphs don't visually run together), skipping any atoms whose
text is empty after stripping.

```python
"\n\n".join(atom.text.strip() for atom in atoms if atom.text.strip()).strip()
```

**Example:**
```
atoms = [TextAtom(text="Revenue grew 40%."), TextAtom(text="This was due to marketing.")]
→ "Revenue grew 40%.\n\nThis was due to marketing."
```

This is the function that produces the **final chunk text** that eventually
gets sent to the embedding model.

---

## 13. Adding Context Before Embedding

### `build_embedding_text(document_record, section, chunk_text) -> str`
Wraps the raw chunk text with a small "header" of metadata before sending it
to the embedding model.

It builds a heading path like `"Overview > Financial Results"` by joining
the section's `heading_path` list, then prepends:
- `Document: <title>`
- `Section: <heading path>`
- `Publication year: <year>` (only if present)
- `Document type: <type>` (only if present)
- `Domain: <domain>` (only if present)
- a blank line
- the actual chunk text

**Why:** Embeddings generally produce better, more discriminative vectors
when the text includes some surrounding context, not just an isolated
sentence. Two chunks that say "Revenue grew 40%" from two totally different
documents/companies become distinguishable once you prepend which document
and section they came from.

**Example output:**
```
Document: Acme Turnaround Case Study
Section: Overview > Financial Results
Publication year: 2023
Document type: case_study

Sales grew 40% due to the new marketing campaign.
```

This exact string — not the raw chunk text alone — is what should be passed
to Google's embedding API.

---

## 14. Building "Parent" Records for Whole Sections

### `create_parent_record(section, document_record, atoms) -> dict[str, Any]`
While `chunk_atoms` produces small pieces meant for embedding/search, this
function builds a **bigger "parent" record for the entire section** —
combining *all* of its atoms into one full-text blob, with rich metadata.

This is the **parent-child retrieval pattern**: small chunks are searched
against (better precision), but when a chunk matches a query, you can show
the user the full parent section for better context and a proper citation.

What it computes/includes:
- `text` — the full combined text of the whole section (via
  `combine_atom_text`).
- `page_start` / `page_end` — the minimum and maximum page numbers spanned
  by the section's atoms (falls back to the section's own declared page
  range if there are no atoms).
- `source_block_ids` — a **de-duplicated, order-preserving** list of every
  block ID that contributed to this section
  (`dict.fromkeys(...)` is a common Python trick for "unique items,
  keeping original order").
- `character_count` / `token_count_approx` — size stats for the full
  section.
- `contains_code` — `True` if *any* atom in the section looks like code.
- `indexable` — whether this section should actually be indexed for search
  (defaults to `True` unless the section says otherwise — e.g. a
  table-of-contents section might be marked non-indexable).
- `freshness_warning` — carried over from the document record, e.g. to flag
  "this document may be outdated" in search results.
- `source` / `citation` — metadata used to show the user exactly where this
  content came from (document title, filename, section title, page
  numbers) when displaying search results.

**In short:** this record is the "show the user where this came from and
give them the full surrounding text" companion to the small, precise search
chunks produced by `chunk_atoms`.

---

## How All the Pieces Fit Together (End-to-End Flow)

```
1. load_manifest()              → get list of documents to process
2. build_source_block_lookup()  → flatten each document's PDF pages/blocks
                                   into an ID → text lookup table
3. get_chunk_profile()          → decide max/overlap/min token settings
                                   for this document
4. For each section in the document:
     a. build_section_atoms()       → gather the section's text as atoms
                                        (splitting oversized blocks via
                                        split_text_by_token_budget)
     b. chunk_atoms()                → pack atoms into overlapping,
                                        budget-respecting chunks
                                        (using select_overlap_atoms
                                        internally)
     c. For each chunk:
          combine_atom_text()        → turn atoms back into one string
          build_embedding_text()     → add document/section context header
          calculate_text_hash()      → fingerprint for dedup detection
          → this is what gets sent to the embedding API
     d. create_parent_record()       → also save the full section as a
                                        "parent" record for citations
5. write_json() / write_jsonl()  → save everything to data/processed/
```

---

## Where Google's Embedding Model Specifically Matters

Almost everything above is **tokenizer-agnostic** — the chunking strategy,
overlap logic, metadata building, hashing, and file I/O all work the same
no matter which embedding model you eventually call.

The **one function that's an approximation, not the real thing**, is:

```python
def approximate_token_count(text: str) -> int:
    return len(TOKEN_PATTERN.findall(text))
```

Google's embedding models use a SentencePiece-based tokenizer internally,
which typically produces **more tokens per word** than this simple
regex-based word/punctuation counter — especially for:
- Non-English text
- Code snippets (flagged here via `likely_code_block`)
- Numbers, URLs, camelCase identifiers, hyphenated words

So your actual chunks may run a bit "bigger" in Google's real token count
than this script assumes. Two practical options:

1. **Add safety margin** — lower your `maximum_tokens` profile values a bit
   below Google's real input limit, so the regex's undercount doesn't cause
   you to exceed it.
2. **Validate with the real tokenizer at the boundary** — after
   `combine_atom_text()` produces the final chunk text, do one real
   `count_tokens` call (via Google's SDK) before sending to the embeddings
   API, and re-split anything that comes back over the limit. This keeps
   the fast regex approach for the bulk of the chunking logic, while
   guaranteeing correctness right where it matters most.