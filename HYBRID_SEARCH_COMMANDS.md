# Hybrid Search Commands

## Why the command error happened

The script requires one operation command after the Python filename:

```text
index
```

or:

```text
search
```

The following command only starts the script without selecting an operation:

```powershell
& C:\Python312\python.exe .\src\ingestion\hybrid_search.py
```

Therefore, the argument parser displays:

```text
usage: hybrid_search.py [-h] {index,search} ...
hybrid_search.py: error: the following arguments are required: command
```

This is not a model failure. The script is asking whether it should build the index or perform a search.

## Operation flow

```text
First time or after changing chunks
                │
                ▼
              index
                │
                ▼
    Dense + sparse vectors in Qdrant
                │
                ▼
              search
                │
                ▼
       Retrieved evidence and context
```

## 1. Build the hybrid index

Run indexing after producing `parents.jsonl` and `chunks.jsonl`:

```powershell
& C:\Python312\python.exe .\src\ingestion\hybrid_search.py index --device cpu
```

The indexing operation performs:

```text
chunks.jsonl
    │
    ├── EmbeddingGemma ──> dense semantic vectors
    │
    └── BM25 ────────────> sparse lexical vectors
                            │
                            ▼
                   Qdrant hybrid index
```

### Rebuild an existing index

Use `--recreate` when chunks, vector settings, or embedding models have changed:

```powershell
& C:\Python312\python.exe .\src\ingestion\hybrid_search.py index --device cpu --recreate
```

> `--recreate` deletes and rebuilds the existing collection. Do not use it for every search.

### Index one document only

```powershell
& C:\Python312\python.exe .\src\ingestion\hybrid_search.py index `
  --document modern-web-penetration-testing-2016 `
  --device cpu
```

The `--document` option may be supplied more than once:

```powershell
& C:\Python312\python.exe .\src\ingestion\hybrid_search.py index `
  --document modern-web-penetration-testing-2016 `
  --document real-world-bug-hunting-2019 `
  --device cpu
```

## 2. Run hybrid search

Indexing must finish successfully before searching.

```powershell
& C:\Python312\python.exe .\src\ingestion\hybrid_search.py search `
  --query "How does SQL injection bypass authentication?" `
  --device cpu
```

This performs:

```text
Question
   │
   ├── Dense semantic search
   │
   └── Sparse BM25 search
              │
              ▼
          RRF fusion
              │
              ▼
       Best child chunks
              │
              ▼
    Parent/neighbour expansion
              │
              ▼
      Agent-ready evidence
```

## 3. Print machine-readable JSON

```powershell
& C:\Python312\python.exe .\src\ingestion\hybrid_search.py search `
  --query "How does SQL injection bypass authentication?" `
  --device cpu `
  --json
```

## 4. Search one document only

```powershell
& C:\Python312\python.exe .\src\ingestion\hybrid_search.py search `
  --query "Explain parameterized SQL queries" `
  --document modern-web-penetration-testing-2016 `
  --device cpu
```

## 5. Control the number of results

```powershell
& C:\Python312\python.exe .\src\ingestion\hybrid_search.py search `
  --query "Explain parameterized SQL queries" `
  --candidate-limit 30 `
  --top-k 8 `
  --max-per-parent 2 `
  --device cpu
```

| Option | Meaning |
|---|---|
| `--candidate-limit` | Number of candidates requested before the final selection |
| `--top-k` | Maximum number of final child results |
| `--max-per-parent` | Maximum results allowed from the same parent section |

`--candidate-limit` must be greater than or equal to `--top-k`.

## 6. Choose context expansion

Available context modes:

| Mode | Behaviour |
|---|---|
| `none` | Return search hits without expanded context |
| `child` | Return only the matched child text |
| `neighbors` | Return matched children with nearby child chunks |
| `parent` | Return the complete parent section |
| `auto` | Use the parent when small enough; otherwise use neighbouring children |

Example:

```powershell
& C:\Python312\python.exe .\src\ingestion\hybrid_search.py search `
  --query "Explain authentication bypass" `
  --context-mode auto `
  --neighbor-window 1 `
  --parent-token-limit 1400 `
  --context-token-budget 6000 `
  --device cpu
```

## 7. Display command help

Show the two supported operations:

```powershell
& C:\Python312\python.exe .\src\ingestion\hybrid_search.py -h
```

Show indexing options:

```powershell
& C:\Python312\python.exe .\src\ingestion\hybrid_search.py index -h
```

Show search options:

```powershell
& C:\Python312\python.exe .\src\ingestion\hybrid_search.py search -h
```

## TensorFlow and oneDNN messages

Messages such as the following are informational:

```text
oneDNN custom operations are on
```

```text
tf.losses.sparse_softmax_cross_entropy is deprecated
```

They come from libraries loaded by the embedding-model dependencies. They are not the cause of the missing-command error.

The actual error was:

```text
the following arguments are required: command
```

## Normal working sequence

```powershell
# Step 1: build the index
& C:\Python312\python.exe .\src\ingestion\hybrid_search.py index --device cpu

# Step 2: ask a question
& C:\Python312\python.exe .\src\ingestion\hybrid_search.py search `
  --query "How does SQL injection bypass authentication?" `
  --device cpu
```
