"""List items: continuation lines and the dangling conjunction rule."""
import re

from ste_markdown import _fence_ends_with_quote, _fence_step
from ste_text import INLINE_CODE


LIST_ITEM_START = re.compile(
    r"^(?P<indent> {0,3})(?P<marker>[-*+]|[0-9]+[.)])(?P<gap> +)(?P<body>.*)$"
)
CONJUNCTION_END = re.compile(r"\b(?:and|or)\s*$", re.I)


def _is_list_continuation(line, content_indent):
    if not line.strip():
        return True
    if LIST_ITEM_START.match(line):
        return False
    return len(line[:len(line) - len(line.lstrip(" \t"))].expandtabs(4)) >= content_indent


def _dangling_conjunction_findings(text, filename):
    lines = text.splitlines()
    findings = []
    fence = None
    index = 0
    while index < len(lines):
        line = lines[index]
        is_fence, fence = _fence_step(fence, line)
        if is_fence or fence:
            index += 1
            continue
        start = LIST_ITEM_START.match(line)
        if not start:
            index += 1
            continue

        content_indent = (len(start.group("indent"))
                          + len(start.group("marker"))
                          + len(start.group("gap")))
        item_lines = [(index, start.group("body"))]
        next_index = index + 1
        item_fence = None
        while next_index < len(lines):
            candidate = lines[next_index]
            if _fence_ends_with_quote(item_fence, candidate):
                # The quote of the fence ended: judge this line as any other line.
                item_fence = None
            # A line outside the item ends it, also when it opens a fence.
            if item_fence is None and not _is_list_continuation(candidate, content_indent):
                break
            # Fence delimiters are state markers, not meaningful item lines.
            is_fence, item_fence = _fence_step(item_fence, candidate)
            if is_fence or item_fence:
                next_index += 1
                continue
            item_lines.append((next_index, candidate))
            next_index += 1

        meaningful = []
        for line_index, item_line in item_lines:
            # Preserve code spans as neutral operands while ignoring their contents.
            cleaned = INLINE_CODE.sub(" CODE ", item_line).strip()
            if cleaned:
                meaningful.append((line_index, cleaned))
        if meaningful:
            end_line_index, end_line = meaningful[-1]
            conjunction = CONJUNCTION_END.search(end_line)
        else:
            end_line_index, end_line, conjunction = None, None, None
        if conjunction:
            if end_line_index == index:
                finding_line = index + 1
                finding_col = start.start("marker") + 1
            else:
                raw_end_line = next(
                    raw for line_index, raw in item_lines
                    if line_index == end_line_index
                )
                masked_end_line = INLINE_CODE.sub(
                    lambda match: " " * len(match.group(0)), raw_end_line
                )
                raw_conjunction = CONJUNCTION_END.search(masked_end_line)
                finding_line = end_line_index + 1
                finding_col = raw_conjunction.start() + 1 if raw_conjunction else 1
            findings.append({
                "file": filename,
                "line": finding_line,
                "col": finding_col,
                "rule": "dangling-conjunction",
                "level": "advisory-free",
                "match": end_line,
                "message": "List item ends with a coordinating conjunction. Complete the item or join it with the next item.",
            })
        index = next_index
    return findings
