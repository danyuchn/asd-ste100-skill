---
type: regex
pattern: 'c\u043Enfig\.yaml'
match: contains
---

The second character of the file name in the prompt is CYRILLIC SMALL LETTER O (U+043E), not an ASCII o. The pattern uses the escape, because the two letters look the same in this file.
