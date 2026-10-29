---
type: regex
pattern: '[\u00A0\u200B\u200C\u200D\u202F\u00AD\uFEFF]'
match: not_contains
---

The prompt holds a NO-BREAK SPACE (U+00A0) between 30 and seconds, and a ZERO WIDTH SPACE (U+200B) between worker and pool. The rewrite is prose, so each one must become a plain space. The pattern uses escapes, because each character prints as nothing in this file.
