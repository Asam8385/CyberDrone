# Understanding Regex (Regular Expressions)

A quick reference for reading the `re` patterns used in the command-detection code, plus general regex syntax.

---

## The Building Blocks

| Symbol | Meaning | Example |
|---|---|---|
| `^` | Start of the line | `^abc` = line must *begin* with "abc" |
| `$` | End of the line | `abc$` = line must *end* with "abc" |
| `\s` | Any whitespace (space, tab) | `a\sb` matches "a b" |
| `\s+` | One or more whitespace chars | matches "a   b" too |
| `\s*` | Zero or more whitespace | optional spacing |
| `.` | Any single character | `a.c` matches "abc", "axc", etc. |
| `?` | Previous thing is optional | `colou?r` matches "color" and "colour" |
| `+` | One or more of the previous thing | `a+` matches "a", "aa", "aaa" |
| `*` | Zero or more of the previous thing | `a*` matches "", "a", "aaa" |
| `[abc]` | Any **one** of these characters | `[aeiou]` matches any vowel |
| `[a-z]` | A range | any lowercase letter |
| `[^abc]` | NOT any of these | anything except a, b, c |
| `(?:...)` | Group things together, don't capture | just for grouping/organizing |
| `\|` | OR | `cat\|dog` matches "cat" or "dog" |
| `\.` | A literal dot (escaped) | without `\`, `.` means "any character" |
| `\\` | A literal backslash | needed for Windows paths |
| `{2,}` | Two or more repetitions | `\d{2,}` matches "12", "123", etc. |
| `re.I` | Flag: case-insensitive | makes `SELECT` also match `select` |

---

## How to Read Any Regex (Step by Step)

1. Split it at the `(?:...)` groups — each one is a self-contained sub-piece.
2. Read left to right, one token at a time. A "token" is either one character, one `\x` escape, or one `[...]` character set.
3. For each token, ask: is it **required** (nothing after it) or **optional/repeated** (`?`, `*`, `+`, `{n,}` right after it)?
4. Ignore the Python `r"..."` wrapper — that's just a "raw string" so backslashes aren't double-escaped. The actual pattern is what's inside the quotes.

---

## Worked Examples

### Example 1 — CLI command with a flag

```python
re.compile(r"^\s*(?:sudo\s+)?[a-zA-Z0-9_.-]+\s+--?[a-zA-Z]")
```

| Piece | Meaning |
|---|---|
| `^\s*` | start of line, allow leading spaces |
| `(?:sudo\s+)?` | optionally, the word "sudo" + a space |
| `[a-zA-Z0-9_.-]+` | the command name (letters/digits/`_`/`.`/`-`) |
| `\s+` | a space |
| `--?` | a dash, or two dashes |
| `[a-zA-Z]` | a letter right after the dash(es) — the flag itself |

**Plain English:** "An optional `sudo`, then a command name, then a space, then a flag starting with `-` or `--`."

- ✅ Matches: `nmap -sV`, `sudo apt-get --install`, `curl -X`
- ❌ Doesn't match: `nmap` (no flag), `just a sentence`

---

### Example 2 — Environment variable assignment

```python
re.compile(r"^\s*[A-Z_][A-Z0-9_]*=")
```

| Piece | Meaning |
|---|---|
| `^\s*` | start of line, optional spaces |
| `[A-Z_]` | **one** uppercase letter or underscore (must start with this) |
| `[A-Z0-9_]*` | zero or more uppercase letters/digits/underscores after that |
| `=` | a literal equals sign |

- ✅ Matches: `API_KEY=`, `DEBUG=`, `_TOKEN=`
- ❌ Doesn't match: `apiKey=` (lowercase), `1ABC=` (starts with a digit)

---

### Example 3 — HTTP request line

```python
re.compile(r"^\s*(?:GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)\s+/")
```

| Piece | Meaning |
|---|---|
| `^\s*` | start of line, optional spaces |
| `(?:GET\|POST\|PUT\|PATCH\|DELETE\|OPTIONS\|HEAD)` | one of these exact words |
| `\s+` | a space |
| `/` | a literal forward slash (the start of a path) |

- ✅ Matches: `GET /api/users`, `POST /login`
- ❌ Doesn't match: `GET the data` (no leading slash)

---

### Example 4 — SQL statement (case-insensitive)

```python
re.compile(r"^\s*(?:SELECT|INSERT|UPDATE|DELETE|UNION)\s+", re.I)
```

Same structure as Example 3, but the `re.I` flag at the end means the match ignores case — so it also matches `select`, `Select`, `sElEcT`.

---

## A Free Tool That Makes This Click

Paste any pattern into **[regex101.com](https://regex101.com)** and set the flavor to **Python**. It:

- Color-codes every piece of the pattern
- Explains each token in plain English in a side panel
- Lets you test the pattern against your own sample text live

This is the fastest way to build intuition — much faster than reading tables.

---

## Quick Mental Model

Think of regex as a **very literal-minded find**: you're describing the *shape* of text you want, character by character, using symbols instead of prose. Once you can name what each symbol does in isolation, reading a long pattern is just reading the symbols left to right and chaining the meanings together.




### What is a regex, at the most basic level?

A **regex** (regular expression) is just a **search pattern for text** — a mini-language for describing "what does the text I'm looking for look like?"

Instead of searching for one exact word, you describe a _shape_ of text, and the computer finds anything matching that shape.

Example: instead of searching for the exact word "cat", you could write a pattern that means "any word that starts with a letter and has 3 letters" — and it would match "cat", "dog", "run", etc.

### The building blocks used in our pattern

Our pattern is: \\w+|\[^\\w\\s\]

Let's learn each piece **one at a time**, super slowly.

#### Piece 1: \\w — "a word character"

\\w is a **shortcut symbol** that means: _"any single letter, digit, or underscore."_

So \\w matches ONE character from this list: a b c ... z A B C ... Z 0 1 2 ... 9 \_

It does **not** match: spaces, punctuation like . , !, symbols like % #.

Think of \\w as a stamp that checks one character at a time and asks: _"is this a letter, digit, or underscore?"_ If yes → match. If no → no match.

#### Piece 2: + — "one or more of the thing before it"

\+ doesn't match a character itself — it's a **modifier** that changes the meaning of whatever comes right before it.

\+ means: _"one or more repeats of the previous thing."_

So \\w+ means: _"one or more word characters, back to back."_

**Example:** In the text hello, \\w+ doesn't just match the letter h — it greedily matches h, then checks "is the next character also \\w? yes, keep going" — and keeps grabbing letters until it hits something that ISN'T a word character (like a space). So \\w+ matches the whole word hello as one single match.

#### Piece 3: | — "OR"

| is just the word **"or"**. It lets you say "match THIS pattern, or THAT pattern."

So A|B means: "match A, or if that doesn't work, try matching B."

In our pattern \\w+|\[^\\w\\s\], the | splits it into two options:

*   Option 1: \\w+
    
*   Option 2: \[^\\w\\s\]
    

At every position in the text, the regex tries option 1 first; if that can't match starting there, it tries option 2.

#### Piece 4: \[...\] — "a character class" (a menu of choices)

Square brackets \[ \] mean: _"match exactly ONE character, and it has to be one of the characters listed inside these brackets."_

Example: \[abc\] matches a single character that is either a, b, or c. Just one character — not all three.

#### Piece 5: ^ inside brackets — "NOT" (negation)

Normally \[abc\] means "match a, b, or c." But if you put a ^ as the **very first character** inside the brackets, it flips the meaning to **negation**: _"match any ONE character that is NOT in this list."_

Example: \[^abc\] matches any single character that is **anything except** a, b, or c. So it would match d, 9, !, a space — anything, as long as it's not a, b, or c.

#### Piece 6: \\s — "a whitespace character"

Like \\w, this is another shortcut symbol. \\s matches ONE character that is whitespace — a space, a tab, or a newline (the invisible characters used for spacing/line breaks).

#### Now let's combine pieces 4, 5, 6: \[^\\w\\s\]

Read it left to right:

*   \[^ → "match one character that is NOT any of the following"
    
*   \\w → word characters (letters/digits/underscore)
    
*   \\s → whitespace characters (spaces, tabs, newlines)
    
*   \] → end of the list
    

So \[^\\w\\s\] means: **"match exactly one character that is neither a letter/digit/underscore, nor whitespace."**

What's left over, if you rule out letters/digits/underscore AND whitespace? **Punctuation and symbols** — things like . , ! ? % # @ ( ) - " etc.

So \[^\\w\\s\] = "grab one punctuation/symbol character."