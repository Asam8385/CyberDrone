# RAG JSON Structures

This document shows the JSON shapes produced by the current ingestion and chunking scripts.

> Every JSON value is a description in the format `expected type — purpose`. These descriptions explain the schema; they are not real document data.

> For a `.jsonl` file, the code block shows the structure of **one line**. The real file contains many records with the same structure, one JSON object per line.

## File flow

```text
PDF
 ├─ document.json
 ├─ toc.json
 ├─ pages.jsonl
 ├─ images.jsonl
 ├─ tables.jsonl
 └─ extraction-report.json
          │
          ▼
     sections.jsonl
     section-report.json
          │
          ▼
     parents.jsonl
     chunks.jsonl
     chunk-report.json
          │
          ▼
     Qdrant point
          │
          ▼
     retrieval result
```

---

## 1. `document.json`

```python
"""
One object describing the complete source PDF.

It stores document identity, source-file information, classification,
extraction settings, and high-level counts. It does not contain page text.
"""
```

```json
{
  "schema_version": "string — version of this record format",
  "document_id": "string — stable unique ID used to connect every record from this PDF",
  "source_path": "string — configured path to the original PDF",
  "source_filename": "string — original PDF filename",
  "source_sha256": "string — SHA-256 fingerprint used to detect a changed source file",
  "title": "string — human-readable document title",
  "author": "string or null — document author when known",
  "publication_year": "integer — year the document was published",
  "document_type": "string — category such as book or reference manual",
  "domain": "string — subject category used for filtering",
  "chunk_profile": "string — name of the chunk-size configuration selected for this document",
  "freshness_warning": "boolean — whether old content should be treated with extra caution",
  "language": "string — document language code",
  "trust_tier": "integer — configured source-reliability level",
  "page_count": "integer — total number of pages in the PDF",
  "toc_entry_count": "integer — number of extracted table-of-contents entries",
  "table_extraction_enabled": "boolean — whether table detection was enabled",
  "ocr_enabled": "boolean — whether OCR was enabled for this extraction",
  "extractor": "string — library used to extract the PDF",
  "extractor_version": "string — installed extractor-library version",
  "extracted_at": "string — UTC timestamp showing when extraction finished"
}
```

---

## 2. `toc.json`

```python
"""
One JSON array containing the PDF table-of-contents entries.

Each entry represents one heading from the PDF outline. Nested headings use
parent_toc_id to point to their parent entry.
"""
```

```json
[
  {
    "toc_id": "string — unique ID for this outline entry",
    "parent_toc_id": "string or null — ID of the parent outline entry",
    "level": "integer — outline depth such as chapter, section, or subsection",
    "title": "string — heading text from the PDF outline",
    "page_number": "integer — page where the outline entry points"
  }
]
```

---

## 3. `pages.jsonl`

```python
"""
One JSONL record for one PDF page.

A page contains ordered text blocks. A block contains lines, and a line
contains spans. A span is the smallest stored text-and-font unit.

The source_block_id used later is calculated from page_number and block_index;
it is not stored directly in this extraction record.
"""
```

```json
{
  "document_id": "string — ID connecting this page to document.json",
  "page_number": "integer — one-based PDF page number",
  "width": "number — page width in PDF points",
  "height": "number — page height in PDF points",
  "rotation": "integer — page rotation in degrees",
  "text": "string — cleaned text made by joining the usable page blocks",
  "character_count": "integer — number of characters in the cleaned page text",
  "word_count": "integer — approximate number of whitespace-separated words",
  "has_native_text": "boolean — whether the page contains extractable text",
  "extraction_method": "string — method used to obtain the page text",
  "blocks": [
    {
      "block_index": "integer — cleaned block position used by later pipeline stages",
      "source_block_index": "integer — original block position returned by PyMuPDF",
      "bbox": [
        "number — left x coordinate",
        "number — top y coordinate",
        "number — right x coordinate",
        "number — bottom y coordinate"
      ],
      "text": "string — text created by joining this block's lines",
      "lines": [
        {
          "text": "string — text created by joining the line's spans",
          "bbox": [
            "number — left x coordinate",
            "number — top y coordinate",
            "number — right x coordinate",
            "number — bottom y coordinate"
          ],
          "direction": [
            "number — horizontal writing-direction component",
            "number — vertical writing-direction component"
          ],
          "writing_mode": "integer — PyMuPDF writing-mode code",
          "spans": [
            {
              "text": "string — smallest stored piece of extracted text",
              "bbox": [
                "number — left x coordinate",
                "number — top y coordinate",
                "number — right x coordinate",
                "number — bottom y coordinate"
              ],
              "origin": [
                "number — text origin x coordinate",
                "number — text origin y coordinate"
              ],
              "font": "string — font name reported by PyMuPDF",
              "font_size": "number — font size reported by PyMuPDF",
              "flags": "integer — original PyMuPDF font-style bit flags",
              "is_bold": "boolean — whether the font flags indicate bold text",
              "is_italic": "boolean — whether the font flags indicate italic text",
              "is_monospaced": "boolean — whether the font flags indicate fixed-width text",
              "is_superscript": "boolean — whether the font flags indicate superscript text",
              "color": "integer or null — encoded text colour reported by PyMuPDF"
            }
          ],
          "monospaced_ratio": "number — proportion of line characters using a monospaced font",
          "contains_command_pattern": "boolean — whether the line resembles a command, URL, or terminal input"
        }
      ],
      "likely_code_block": "boolean — whether the block is probably code or terminal text",
      "code_confidence": "number — strength of the code-block heuristic",
      "is_repeated_margin": "boolean — whether this block is a repeated header or footer"
    }
  ],
  "image_ids": [
    "string — ID of an image record belonging to this page"
  ],
  "image_count": "integer — number of image metadata records on this page",
  "max_image_coverage_ratio": "number — largest fraction of the page covered by one image",
  "table_ids": [
    "string — ID of a table record belonging to this page"
  ],
  "table_count": "integer — number of detected tables on this page",
  "removed_margin_text": [
    "string — repeated header or footer text removed from searchable page text"
  ]
}
```

---

## 4. `images.jsonl`

```python
"""
One JSONL record for one image placement found inside a PDF page.

Only metadata is stored. The image bytes are not saved, and OCR is not run.
"""
```

```json
{
  "image_id": "string — unique ID for this image placement",
  "document_id": "string — source document ID",
  "page_number": "integer — page containing the image",
  "image_index": "integer — image order on that page",
  "xref": "integer or null — internal PDF cross-reference number",
  "bbox": [
    "number — left x coordinate",
    "number — top y coordinate",
    "number — right x coordinate",
    "number — bottom y coordinate"
  ],
  "width": "integer or null — image pixel width",
  "height": "integer or null — image pixel height",
  "bits_per_component": "integer or null — colour depth for each image component",
  "colorspace": "integer or null — PDF colour-space code",
  "colorspace_name": "string or null — readable colour-space name",
  "x_resolution": "number or null — horizontal image resolution",
  "y_resolution": "number or null — vertical image resolution",
  "digest": "string or null — image-content fingerprint",
  "page_coverage_ratio": "number — fraction of the page covered by the image"
}
```

---

## 5. `tables.jsonl`

```python
"""
One JSONL record for one table detected on a PDF page.

The record contains its position, size, extracted cell matrix, and optional
Markdown representation.
"""
```

```json
{
  "table_id": "string — unique ID for this detected table",
  "document_id": "string — source document ID",
  "page_number": "integer — page containing the table",
  "table_index": "integer — table order on that page",
  "bbox": [
    "number — left x coordinate",
    "number — top y coordinate",
    "number — right x coordinate",
    "number — bottom y coordinate"
  ],
  "row_count": "integer — number of extracted table rows",
  "column_count": "integer — largest number of cells found in any row",
  "cells": [
    [
      "string or null — extracted content of one table cell"
    ]
  ],
  "markdown": "string or null — table converted to Markdown when conversion succeeds"
}
```

---

## 6. `extraction-report.json`

```python
"""
One summary object describing the extraction run for a document.

It contains counts, page-quality observations, warnings, and confirmation that
OCR was not used. It is for diagnostics, not retrieval.
"""
```

```json
{
  "schema_version": "string — version of this report format",
  "document_id": "string — document summarized by this report",
  "generated_at": "string — UTC timestamp when the report was created",
  "page_count": "integer — total extracted page records",
  "toc_entry_count": "integer — total table-of-contents entries",
  "total_character_count": "integer — sum of cleaned characters across all pages",
  "empty_page_count": "integer — number of pages with no extracted characters",
  "empty_pages": [
    "integer — page number containing no extracted characters"
  ],
  "low_text_page_count": "integer — number of pages below the low-text threshold",
  "low_text_pages": [
    "integer — page number containing very little text"
  ],
  "image_metadata_count": "integer — total image metadata records",
  "pages_with_images": [
    "integer — page number containing at least one image"
  ],
  "image_only_candidate_pages": [
    "integer — page number containing little text and a large image"
  ],
  "table_count": "integer — total detected table records",
  "pages_with_tables": [
    "integer — page number containing a detected table"
  ],
  "pages_with_code_blocks": [
    "integer — page number containing at least one likely code block"
  ],
  "repeated_margin_signature_count": "integer — number of repeated header/footer patterns detected",
  "warnings": [
    "string — extraction warning requiring review"
  ],
  "ocr_used": "boolean — whether OCR contributed any extracted text"
}
```

---

## 7. `sections.jsonl`

```python
"""
One JSONL record for one detected document section.

The record groups source blocks under a heading. It keeps the complete section
text, the page range, heading hierarchy, source references, and citation data.
"""
```

```json
{
  "schema_version": "string — version of the section record format",
  "section_id": "string — unique stable ID for this detected section",
  "document_id": "string — source document ID",
  "parent_section_id": "string or null — ID of the containing higher-level section",
  "section_number": "integer — section order within the processed document",
  "title": "string — detected section heading",
  "heading_path": [
    "string — one breadcrumb heading from chapter to current section"
  ],
  "level": "integer — heading depth",
  "page_start": "integer — first page touched by this section",
  "page_end": "integer — last page touched by this section",
  "text": "string — complete section text assembled from source blocks",
  "character_count": "integer — number of characters in the section text",
  "word_count": "integer — approximate whitespace-separated word count",
  "source_block_ids": [
    "string — calculated page/block ID identifying an original extracted block"
  ],
  "table_ids": [
    "string — ID of a detected table within the section page range"
  ],
  "contains_code": "boolean — whether any source block is probably code",
  "indexable": "boolean — whether this section is suitable for chunking and search",
  "detection": {
    "method": "string — heading-detection method that created the section",
    "anchor_page": "integer — page where the section heading was anchored",
    "anchor_block_id": "string — source block used as the section heading",
    "anchor_score": "number — confidence score for the selected heading anchor"
  },
  "source": {
    "title": "string — source document title",
    "author": "string or null — source document author",
    "publication_year": "integer — source publication year",
    "source_filename": "string — original PDF filename",
    "source_sha256": "string — fingerprint of the source PDF"
  },
  "citation": {
    "document_title": "string — title displayed in an answer citation",
    "section_title": "string — section displayed in an answer citation",
    "page_start": "integer — first cited page",
    "page_end": "integer — last cited page"
  },
  "quality_flags": [
    "string — quality warning such as a short section or low-confidence anchor"
  ]
}
```

---

## 8. `section-report.json`

```python
"""
One summary object describing section detection for one document.

It helps you inspect heading quality and identify short, fallback, or
low-confidence sections. It is not embedded or indexed.
"""
```

```json
{
  "schema_version": "string — version of this report format",
  "document_id": "string — document summarized by this report",
  "detection_mode": "string — overall heading-detection strategy used",
  "body_font_size": "number — estimated normal paragraph font size",
  "heading_event_count": "integer — number of heading-start events detected",
  "section_count": "integer — total section records produced",
  "indexable_section_count": "integer — sections accepted for chunking and search",
  "non_indexable_section_count": "integer — sections rejected from indexing",
  "sections_with_code_count": "integer — sections containing likely code blocks",
  "short_section_count": "integer — sections below the configured minimum size",
  "fallback_anchor_count": "integer — sections created using fallback heading logic",
  "low_confidence_anchor_count": "integer — sections whose heading anchors need review",
  "warnings": [
    "string — section-detection warning"
  ]
}
```

---

## 9. `parents.jsonl`

```python
"""
One JSONL record for one complete indexable section.

The parent preserves the full section for context expansion. Search normally
finds a child first and then follows parent_id to this record when more context
is required.
"""
```

```json
{
  "schema_version": "string — version of the parent record format",
  "parent_id": "string — unique parent ID followed by child chunks during context expansion",
  "section_id": "string — originating section ID; currently the same logical ID as parent_id",
  "document_id": "string — source document ID",
  "parent_section_id": "string or null — higher-level section ID when one exists",
  "title": "string — section title",
  "heading_path": [
    "string — one breadcrumb heading from chapter to current section"
  ],
  "level": "integer or null — heading depth",
  "page_start": "integer — first page represented by this parent",
  "page_end": "integer — last page represented by this parent",
  "text": "string — complete parent-section text",
  "character_count": "integer — number of characters in the parent text",
  "token_count_approx": "integer — approximate number of tokens in the parent text",
  "source_block_ids": [
    "string — original page/block ID included in this parent"
  ],
  "contains_code": "boolean — whether the parent includes likely code content",
  "indexable": "boolean — whether the source section was accepted for indexing",
  "freshness_warning": "boolean — whether document age should be highlighted",
  "source": {
    "title": "string — source document title",
    "author": "string or null — source author",
    "publication_year": "integer — source publication year",
    "source_filename": "string — original PDF filename",
    "source_sha256": "string — fingerprint of the source PDF"
  },
  "citation": {
    "document_title": "string — document title used in citations",
    "section_title": "string — section title used in citations",
    "page_start": "integer — first cited page",
    "page_end": "integer — last cited page"
  },
  "content_hash": "string — normalized text fingerprint used for duplicate detection"
}
```

---

## 10. `chunks.jsonl`

```python
"""
One JSONL record for one searchable child chunk.

This is the main record sent to the embedding models and vector database.
parent_id connects the small search result back to its complete parent section.
"""
```

```json
{
  "schema_version": "string — version of the child-chunk record format",
  "chunk_id": "string — unique ID for this searchable child",
  "parent_id": "string — ID used to load the complete parent section",
  "section_id": "string — section from which the child was created",
  "document_id": "string — source document ID",
  "chunk_number": "integer — child order within the section",
  "title": "string — section title associated with the child",
  "heading_path": [
    "string — one breadcrumb heading supplied to retrieval"
  ],
  "text": "string — readable child text returned as evidence",
  "embedding_text": "string — child text prefixed with document and heading context for dense embedding",
  "page_start": "integer — first page represented by this child",
  "page_end": "integer — last page represented by this child",
  "source_block_ids": [
    "string — original page/block ID included in this child"
  ],
  "character_count": "integer — number of characters in child text",
  "token_count_approx": "integer — approximate child token count",
  "contains_code": "boolean — whether the child contains likely code content",
  "freshness_warning": "boolean — whether document age should be highlighted",
  "source": {
    "title": "string — source document title",
    "author": "string or null — source author",
    "publication_year": "integer — source publication year",
    "source_filename": "string — original PDF filename",
    "source_sha256": "string — fingerprint of the source PDF"
  },
  "citation": {
    "document_title": "string — document title used in citations",
    "section_title": "string — section title used in citations",
    "page_start": "integer — first cited page",
    "page_end": "integer — last cited page"
  },
  "quality_flags": [
    "string — chunk warning such as short-chunk or contains-code"
  ],
  "content_hash": "string — normalized text fingerprint used for deduplication"
}
```

---

## 11. `chunk-report.json`

```python
"""
One summary object describing parent and child creation for a document.

It reports chunk sizes, skipped or missing source blocks, duplicates, and code
coverage. It is for pipeline quality checks, not search.
"""
```

```json
{
  "schema_version": "string — version of this chunk-report format",
  "document_id": "string — document summarized by this report",
  "profile": {
    "maximum_tokens": "integer — largest permitted approximate child size",
    "overlap_tokens": "integer — approximate previous-content budget copied into the next child",
    "minimum_tokens": "integer — size below which a child receives a short-chunk warning"
  },
  "source_section_count": "integer — total section records supplied to chunking",
  "indexable_section_count": "integer — source sections accepted for parent/child creation",
  "parent_count": "integer — complete parent records produced",
  "chunk_count": "integer — unique searchable child records produced",
  "duplicate_chunk_count": "integer — duplicate children removed using content hashes",
  "missing_source_block_count": "integer — referenced blocks not found in pages.jsonl",
  "missing_source_blocks": [
    "string — source_block_id that could not be resolved"
  ],
  "minimum_chunk_tokens": "integer — smallest approximate child size produced",
  "maximum_chunk_tokens": "integer — largest approximate child size produced",
  "average_chunk_tokens": "number — average approximate child size",
  "short_chunk_count": "integer — children carrying the short-chunk quality flag",
  "chunks_with_code_count": "integer — children containing likely code blocks"
}
```

---

## 12. Qdrant point structure

```python
"""
Conceptual structure of one child chunk after hybrid indexing.

This is a database point rather than one of the current JSONL files. The dense
vector stores semantic meaning. The sparse vector stores token indexes and
BM25-style weights. The payload keeps identifiers, text, and citation metadata.
"""
```

```json
{
  "id": "string or UUID — stable Qdrant point ID derived from the child chunk ID",
  "vector": {
    "dense": [
      "number — one coordinate in the dense semantic embedding"
    ],
    "sparse": {
      "indices": [
        "integer — token-feature index present in this child"
      ],
      "values": [
        "number — sparse BM25-style weight corresponding to the same index position"
      ]
    }
  },
  "payload": {
    "schema_version": "string — originating child-chunk schema version",
    "chunk_id": "string — searchable child ID",
    "parent_id": "string — parent section ID used for context expansion",
    "section_id": "string — source section ID",
    "document_id": "string — source document ID used for filtering",
    "chunk_number": "integer — child order inside the section",
    "title": "string — section title shown with the result",
    "heading_path": [
      "string — one breadcrumb heading"
    ],
    "text": "string — readable evidence returned after vector matching",
    "page_start": "integer — first page represented by this child",
    "page_end": "integer — last page represented by this child",
    "source_block_ids": [
      "string — original page/block ID represented by this child"
    ],
    "contains_code": "boolean — whether the child contains likely code",
    "freshness_warning": "boolean — whether source age should be highlighted",
    "source": {
      "title": "string — source document title",
      "author": "string or null — source author",
      "publication_year": "integer — source publication year",
      "source_filename": "string — source PDF filename",
      "source_sha256": "string — source PDF fingerprint"
    },
    "citation": {
      "document_title": "string — document title used in citations",
      "section_title": "string — section title used in citations",
      "page_start": "integer — first cited page",
      "page_end": "integer — last cited page"
    },
    "quality_flags": [
      "string — quality warning copied from the child record"
    ],
    "content_hash": "string — normalized child-text fingerprint"
  }
}
```

---

## 13. Hybrid retrieval result structure

```python
"""
Recommended structure returned by the completed retrieval layer to the agent.

It separates the original question, ranked child hits, and expanded contexts.
The agent reads context text and citations; it does not need to read vectors.
"""
```

```json
{
  "query": "string — original natural-language question",
  "filters": {
    "document_ids": [
      "string — allowed source document ID"
    ],
    "domains": [
      "string — allowed subject domain"
    ],
    "contains_code": "boolean or null — optional requirement for code-containing results"
  },
  "retrieval": {
    "dense_candidate_count": "integer — number of semantic candidates requested before fusion",
    "sparse_candidate_count": "integer — number of BM25 candidates requested before fusion",
    "fusion_method": "string — ranking-fusion algorithm used to combine both lists",
    "final_top_k": "integer — maximum fused child hits retained"
  },
  "hits": [
    {
      "rank": "integer — final position after hybrid fusion",
      "score": "number — fused relevance score used for ordering",
      "chunk_id": "string — matched child ID",
      "parent_id": "string — parent ID available for context expansion",
      "document_id": "string — source document ID",
      "section_id": "string — source section ID",
      "title": "string — matched section title",
      "page_start": "integer — first page represented by the hit",
      "page_end": "integer — last page represented by the hit",
      "text": "string — matched child text",
      "citation": {
        "document_title": "string — title displayed in the citation",
        "section_title": "string — section displayed in the citation",
        "page_start": "integer — first cited page",
        "page_end": "integer — last cited page"
      }
    }
  ],
  "contexts": [
    {
      "context_strategy": "string — child, neighbour, or parent expansion strategy",
      "matched_chunk_ids": [
        "string — winning or neighbouring child included in this context"
      ],
      "parent_id": "string — parent section represented by this context",
      "document_id": "string — source document ID",
      "section_id": "string — source section ID",
      "title": "string — section title",
      "page_start": "integer — first page represented by the final context",
      "page_end": "integer — last page represented by the final context",
      "text": "string — deduplicated evidence sent to the agent",
      "token_count_approx": "integer — estimated context size used for budget control",
      "citation": {
        "document_title": "string — title displayed in the citation",
        "section_title": "string — section displayed in the citation",
        "page_start": "integer — first cited page",
        "page_end": "integer — last cited page"
      }
    }
  ]
}
```

---

## Which records are used for retrieval?

```python
"""
pages.jsonl and sections.jsonl are processing sources.
parents.jsonl provides larger context.
chunks.jsonl provides the small searchable records.
Qdrant stores the searchable dense and sparse representations.
Reports are used for quality checks and are not normally searched.
"""
```

| Structure | Main purpose | Put in the vector index? |
|---|---|---:|
| `document.json` | Document metadata | No; selected metadata may be copied into payloads |
| `toc.json` | Original PDF outline | No |
| `pages.jsonl` | Extraction source of truth | No |
| `images.jsonl` | Image metadata | No |
| `tables.jsonl` | Extracted table data | Only later if table retrieval is implemented |
| `sections.jsonl` | Detected semantic boundaries | No |
| `parents.jsonl` | Full context sections | Usually kept in a lookup store |
| `chunks.jsonl` | Small searchable child records | Yes |
| Report files | Pipeline diagnostics | No |
| Qdrant point | Dense, sparse, and payload data | This is the vector index record |
| Retrieval result | Evidence returned to the agent | No; created at query time |
