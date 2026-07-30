# Function Reference — Section Builder Script

This document breaks down every function in the script and its responsibility, grouped by role in the pipeline.

## I/O Helpers

| Function | Responsibility |
|---|---|
| `load_json` | Reads a JSON file into memory. |
| `write_json` | Writes JSON atomically — writes to a `.tmp` file, then renames, so a crash mid-write can't corrupt the output. |
| `load_jsonl` | Reads a JSON Lines file (one record per line), raising a clear error with line number on malformed JSON. |
| `write_jsonl` | Writes records as JSON Lines, atomically via temp file + rename. |
| `load_manifest` | Reads `documents.yaml` and returns the list of document configs; raises if empty. |

## Text Normalization

| Function | Responsibility |
|---|---|
| `collapse_whitespace` | Strips soft hyphens/non-breaking spaces and collapses whitespace runs. |
| `normalize_heading` | Unicode-normalizes, lowercases, and strips punctuation for fuzzy text comparison. |
| `heading_skeleton` | Reduces text to just `[a-z0-9]` characters for tight equality/substring checks. |
| `slugify` | Converts a title into a URL/ID-safe slug. |
| `create_title_variants` | Generates alternate forms of a title (e.g. with "Chapter 3:" prefix stripped) to widen matching. |

## Heading Matching

| Function | Responsibility |
|---|---|
| `calculate_heading_similarity` | Scores how well a candidate text block matches an expected TOC title (0–1), combining exact-skeleton match, prefix/substring checks, sequence-matcher ratios, and word overlap. |

## Font / Layout Analysis

| Function | Responsibility |
|---|---|
| `collect_block_font_statistics` | Computes max font size, bold ratio, monospace ratio, and a font-size histogram for a text block. |
| `flatten_pages` | Flattens the page/block tree into an ordered list of "units," skipping repeated margins/empty blocks; also builds a page-number lookup. |
| `detect_body_font_size` | Infers the document's body-text font size as the most common size among non-code units. |

## Heading Detection

| Function | Responsibility |
|---|---|
| `is_numeric_chapter_marker` | Detects blocks that are just a number/roman numeral (large standalone chapter markers). |
| `is_heading_candidate` | Heuristic filter deciding whether a block could be a heading (length, not code/URL, explicit "Chapter/Part/Appendix," oversized font, or bold). |
| `infer_heading_level` | Assigns heading level 1/2/3 based on explicit markers, a preceding large numeric marker, or relative font size. |

## TOC-Based Section Building

| Function | Responsibility |
|---|---|
| `create_unit_page_map` | Groups units by page number for fast lookup. |
| `find_toc_anchor` | For one TOC entry, finds the best-matching text unit on nearby pages, with tiered fallback (heading fallback → any-block fallback → unresolved). |
| `build_toc_events` | Runs `find_toc_anchor` across the whole TOC in order, ensuring anchors are monotonic and non-reused, and collects unresolved-entry warnings. |

## Font-Based Section Building (no/ignored TOC)

| Function | Responsibility |
|---|---|
| `find_manual_chapter_anchor` | Resolves a manually configured chapter-start hint to a specific block on its page. |
| `build_font_events` | Detects headings purely via font/bold heuristics, applies manual chapter overrides, and reconstructs parent/child hierarchy using a level stack. |

## Assembly into Sections

| Function | Responsibility |
|---|---|
| `build_heading_path` | Walks up `parent_event_id` links to build a breadcrumb title path for a section. |
| `is_indexable_title` | Filters out boilerplate titles (Cover, Copyright, Index, etc.) via regex. |
| `collect_table_ids` | Gathers table IDs from all pages spanned by a section. |
| `build_sections_from_events` | Core assembler — slices unit ranges between events, joins text, computes page span/word counts, resolves parent section IDs, attaches quality flags, and builds the final section record. |
| `build_section_report` | Aggregates per-document stats (section counts, indexable/non-indexable, code sections, warnings) into a summary JSON. |

## Orchestration

| Function | Responsibility |
|---|---|
| `process_document` | Top-level per-document pipeline: load extracted pages/TOC → flatten → detect body font → choose TOC-mode vs font-mode → build events → build sections → write `sections.jsonl` + `section-report.json`. |
| `parse_arguments` | Defines and parses CLI arguments (`--manifest`, `--document`, `--minimum-section-characters`). |
| `main` | Entry point — loads manifest, optionally filters to specific document IDs, processes each, collects failures, and exits non-zero if any failed. |

## Overall Responsibility

This script converts raw per-page/per-block PDF extraction output into a hierarchical, citation-ready **sections dataset** — deciding *where* section boundaries fall (via TOC matching or font heuristics), *what* metadata each section carries, and flagging low-confidence or low-quality results for downstream review.