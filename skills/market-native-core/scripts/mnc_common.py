"""Shared helpers for market-native-core scripts.

Standard library only. Every script imports this module first so that stdout and
stderr can print any script on Windows consoles, and so that file
reading, front matter parsing and term matching behave identically everywhere.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

LOCALE_RE = re.compile(r"^[a-z]{2,3}-[a-z0-9]{2,4}$")
FRONT_MATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---[ \t]*\r?\n?", re.DOTALL)
FIELD_HEADING_RE = re.compile(r"^##\s+([a-z0-9_]+)\s*$")
ARABIC_MARKS_RE = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭـ]")
ARABIC_WORD_RE = re.compile(r"[ء-ي]+")
ARABIC_PREFIXES = ("وال", "فال", "بال", "كال", "لل", "ال")
LATIN_RE = re.compile(r"[A-Za-z]")


def configure_stdio() -> None:
    """Make stdout and stderr UTF-8 regardless of the console code page."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass


def today() -> date:
    return datetime.now(timezone.utc).date()


def read_text(path: Path | str) -> str:
    return Path(path).read_text(encoding="utf-8-sig")


def write_text(path: Path | str, text: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")


def read_json(path: Path | str) -> Any:
    return json.loads(read_text(path))


def write_json(path: Path | str, data: Any) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def is_locale_id(value: str) -> bool:
    """True for `language-market` ids such as `en-us`; False for bare `en`."""
    return bool(LOCALE_RE.match(value))


def language_of(locale_id: str) -> str:
    return locale_id.split("-", 1)[0]


def parse_date(value: Any) -> date | None:
    if not value or not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Front matter (a deliberately small YAML subset: scalars, inline and block lists)
# ---------------------------------------------------------------------------


def _scalar(value: str) -> Any:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in ("null", "~"):
        return None
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    return value


def parse_simple_yaml(block: str) -> dict[str, Any]:
    """Parse `key: value`, `key: [a, b]` and `key:` followed by `- item` lines."""
    data: dict[str, Any] = {}
    current: str | None = None
    for raw in block.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if line[:1] in (" ", "\t") and stripped.startswith("- ") and current:
            existing = data.get(current)
            if not isinstance(existing, list):
                data[current] = []
            data[current].append(_scalar(stripped[2:]))
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        current = key
        if value == "":
            data[key] = None
        elif value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            data[key] = [_scalar(v) for v in inner.split(",")] if inner else []
        else:
            data[key] = _scalar(value)
    return data


def dump_simple_yaml(data: dict[str, Any]) -> str:
    lines: list[str] = []
    for key, value in data.items():
        if isinstance(value, list):
            if not value:
                lines.append(f"{key}: []")
            else:
                lines.append(f"{key}:")
                lines.extend(f"  - {item}" for item in value)
        elif value is None:
            lines.append(f"{key}:")
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        else:
            lines.append(f"{key}: {value}")
    return "\n".join(lines) + "\n"


def parse_front_matter(text: str) -> tuple[dict[str, Any], str]:
    """Split a markdown file into (front matter dict, body). No front matter -> ({}, text)."""
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return {}, text
    return parse_simple_yaml(match.group(1)), text[match.end() :]


def parse_fields(body: str) -> dict[str, str]:
    """Split a copy body into `## field_name` sections. Text before the first field is `_intro`."""
    fields: dict[str, list[str]] = {}
    current = "_intro"
    for line in body.splitlines():
        heading = FIELD_HEADING_RE.match(line.strip())
        if heading:
            current = heading.group(1)
            fields.setdefault(current, [])
            continue
        fields.setdefault(current, []).append(line)
    return {name: "\n".join(lines).strip() for name, lines in fields.items()}


# ---------------------------------------------------------------------------
# Term matching
# ---------------------------------------------------------------------------


def _strip_arabic_prefix(match: re.Match[str]) -> str:
    """Drop the definite article and attached conjunction/preposition + article.

    `والتقويم` -> `تقويم`, `الشفاف` -> `شفاف`, `بالتقسيط` -> `تقسيط`. Short remainders are
    left alone so words like `ألم` (pain) are not reduced to a single letter.
    """
    word = match.group(0)
    for prefix in ARABIC_PREFIXES:
        if word.startswith(prefix) and len(word) - len(prefix) >= 3:
            return word[len(prefix) :]
    return word


def normalize_text(text: str) -> str:
    """Lower-case and fold Arabic variants so `أ`/`ا`, `ى`/`ي`, `ة`/`ه`, diacritics and the
    definite article do not prevent a match. Applied to terms and text alike."""
    text = ARABIC_MARKS_RE.sub("", text)
    text = re.sub("[إأآٱ]", "ا", text)
    text = text.replace("ى", "ي").replace("ة", "ه")
    text = text.replace("ؤ", "و").replace("ئ", "ي")
    text = ARABIC_WORD_RE.sub(_strip_arabic_prefix, text)
    text = text.replace("—", " -- ")
    text = text.casefold()
    return re.sub(r"\s+", " ", text)


def contains_term(text_norm: str, term: str) -> bool:
    """Word-boundary match for Latin terms; substring match for scripts without spacing."""
    term_norm = normalize_text(term).strip()
    if not term_norm:
        return False
    if LATIN_RE.search(term_norm):
        pattern = r"(?<![\w])" + re.escape(term_norm) + r"(?![\w])"
        return re.search(pattern, text_norm) is not None
    return term_norm in text_norm


def load_term_list(path: Path | str) -> list[str]:
    """Read a one-term-per-line file, skipping blanks and `#` comments."""
    target = Path(path)
    if not target.exists():
        return []
    terms: list[str] = []
    for line in read_text(target).splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            terms.append(stripped)
    return terms


def dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = normalize_text(item)
        if key and key not in seen:
            seen.add(key)
            out.append(item)
    return out


def approx_tokens(text: str) -> int:
    """Rough token estimate: enough to warn when a pack is too big."""
    return max(1, len(text) // 4)


def skill_root() -> Path:
    return Path(__file__).resolve().parent.parent


def eprint(*args: Any) -> None:
    print(*args, file=sys.stderr)
