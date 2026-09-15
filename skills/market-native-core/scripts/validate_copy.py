#!/usr/bin/env python3
"""Check a copy asset against its context pack.

Errors (exit 1): missing front matter fields, locale or channel mismatch, forbidden or
blocked term present, claim reference that is not eligible, field over its limit.
Warnings (exit 0): no approved term used, a number with no backing claim, an em dash,
a limited field missing from the asset.

Modes:
    --copy FILE --pack PACK.json         check against an existing pack
    --copy FILE --library LIB            rebuild the pack from the asset's front matter
    --library LIB --revalidate           flag assets whose referenced claims changed
    --text FILE --banned LIST.txt        check any text file against a term list

The checks are a floor. They cannot tell whether the copy gives a buyer a reason to
choose; that judgment stays with a person.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import mnc_common as mnc

REQUIRED_META = ("asset_id", "revision", "status", "locale", "channel", "page", "content_scope", "audience")
NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)*")
LIST_MARKER_RE = re.compile(r"(?m)^\s*\d+[.)]\s+")
EM_DASH = "—"


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def note(self, msg: str) -> None:
        self.info.append(msg)

    @property
    def passed(self) -> bool:
        return not self.errors

    def render(self, title: str) -> str:
        lines = [f"# validate: {title}", "", f"result: {'PASS' if self.passed else 'FAIL'} ({len(self.errors)} errors, {len(self.warnings)} warnings)"]
        for label, items in (("errors", self.errors), ("warnings", self.warnings), ("info", self.info)):
            if items:
                lines.append("")
                lines.append(f"## {label}")
                lines.extend(f"- {item}" for item in items)
        return "\n".join(lines) + "\n"

    def as_dict(self) -> dict[str, Any]:
        return {"passed": self.passed, "errors": self.errors, "warnings": self.warnings, "info": self.info}


def check_terms(text_norm: str, terms: list[str], label: str, report: Report, as_error: bool) -> None:
    for term in terms:
        if mnc.contains_term(text_norm, term):
            message = f"{label}: '{term}'"
            report.error(message) if as_error else report.warn(message)


def check_asset(meta: dict[str, Any], fields: dict[str, str], pack: dict[str, Any], report: Report) -> None:
    for key in REQUIRED_META:
        if meta.get(key) in (None, ""):
            report.error(f"front matter missing '{key}'")
    sel = pack.get("selectors", {})
    if meta.get("locale") and meta.get("locale") != sel.get("locale"):
        report.error(f"locale mismatch: asset {meta.get('locale')} vs pack {sel.get('locale')}")
    if meta.get("channel") and meta.get("channel") != sel.get("channel"):
        report.error(f"channel mismatch: asset {meta.get('channel')} vs pack {sel.get('channel')}")

    body_fields = {k: v for k, v in fields.items() if k != "_intro"}
    body_text = "\n".join(body_fields.values())
    text_norm = mnc.normalize_text(body_text)

    check_terms(text_norm, pack.get("forbidden_terms", []), "forbidden term", report, as_error=True)
    check_terms(text_norm, pack.get("blocked_terms", []), "blocked term (awaiting approval)", report, as_error=True)

    eligible = {c.get("claim_id") for c in pack.get("claims", [])}
    refs = meta.get("claim_refs") or []
    if isinstance(refs, str):
        refs = [refs]
    for ref in refs:
        if ref not in eligible:
            report.error(f"claim_refs '{ref}' is not eligible in this pack (wrong status, market, channel, product or audience)")
    if not refs:
        report.warn("claim_refs is empty: the copy promises nothing provable, or the references were not recorded")

    limits = pack.get("limits", {})
    for field, limit in limits.items():
        if field not in body_fields:
            report.warn(f"field '{field}' has a limit but is not in the asset")
            continue
        length = len(body_fields[field].replace("\n", " ").strip())
        if length > int(limit):
            report.error(f"field '{field}' is {length} chars, limit {limit}")
        else:
            report.note(f"field '{field}' {length}/{limit}")

    approved = [t.get("term", "") for t in pack.get("required_terms", []) if t.get("term")]
    used = [t for t in approved if mnc.contains_term(text_norm, t)]
    if approved and not used:
        report.warn("none of the approved glossary terms appear in the copy (generic text signal)")
    elif used:
        report.note(f"approved terms used: {', '.join(used)}")

    claim_text = " ".join(
        f"{c.get('statement', '')} {c.get('evidence', '')}" for c in pack.get("claims", []) if c.get("claim_id") in refs
    )
    for number in sorted(set(NUMBER_RE.findall(LIST_MARKER_RE.sub("", body_text)))):
        if number not in claim_text:
            report.warn(f"number '{number}' appears in the copy but not in any referenced claim")

    if EM_DASH in body_text:
        report.warn(f"em dash present ({body_text.count(EM_DASH)}x); the most reliable AI-text tell")


def load_pack_for_asset(lib: Path, meta: dict[str, Any]) -> dict[str, Any]:
    import build_context  # local import keeps the module optional for --text mode

    sel = {
        "locale": str(meta.get("locale", "")),
        "channel": str(meta.get("channel", "")),
        "page": str(meta.get("page", "")),
        "audience": str(meta.get("audience", "")),
        "product_id": str(meta.get("product_id") or ""),
        "concepts": [],
        "intent": "",
    }
    return build_context.build(lib, sel)


def validate_file(copy_path: Path, pack: dict[str, Any] | None, lib: Path | None) -> Report:
    report = Report()
    meta, body = mnc.parse_front_matter(mnc.read_text(copy_path))
    if not meta:
        report.error("no front matter block found")
        return report
    if pack is None:
        if lib is None:
            report.error("need --pack or --library")
            return report
        try:
            pack = load_pack_for_asset(lib, meta)
        except Exception as exc:  # LibraryError or file errors: report, do not crash
            report.error(f"could not build pack: {exc}")
            return report
    check_asset(meta, mnc.parse_fields(body), pack, report)
    return report


def revalidate(lib: Path) -> Report:
    """Flag approved assets whose referenced claims are no longer verified or eligible."""
    report = Report()
    claims = {c.get("claim_id"): c for c in mnc.read_json(lib / "core" / "claims.json").get("claims", [])}
    today = mnc.today()
    changed = 0
    for path in sorted((lib / "channels").rglob("copy/*/*.md")):
        text = mnc.read_text(path)
        meta, body = mnc.parse_front_matter(text)
        if meta.get("status") != "approved":
            continue
        refs = meta.get("claim_refs") or []
        broken: list[str] = []
        for ref in refs:
            claim = claims.get(ref)
            expires = mnc.parse_date(claim.get("expires")) if claim else None
            if claim is None or claim.get("status") != "verified" or (expires and expires < today):
                broken.append(ref)
            elif not (
                ("*" in (claim.get("eligible_markets") or []) or meta.get("locale") in (claim.get("eligible_markets") or []))
                and ("*" in (claim.get("eligible_channels") or []) or meta.get("channel") in (claim.get("eligible_channels") or []))
            ):
                broken.append(ref)
        if broken:
            meta["status"] = "needs_revalidation"
            meta["validation_status"] = "claims changed: " + ", ".join(broken)
            mnc.write_text(path, "---\n" + mnc.dump_simple_yaml(meta) + "---\n" + body)
            report.warn(f"{path.relative_to(lib).as_posix()} -> needs_revalidation ({', '.join(broken)})")
            changed += 1
    report.note(f"{changed} asset(s) flagged")
    return report


def check_text(text_path: Path, banned_paths: list[Path]) -> Report:
    report = Report()
    terms: list[str] = []
    for path in banned_paths:
        terms.extend(mnc.load_term_list(path))
    text_norm = mnc.normalize_text(mnc.read_text(text_path))
    check_terms(text_norm, mnc.dedupe(terms), "banned term", report, as_error=True)
    report.note(f"checked {len(terms)} terms")
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--copy", help="Copy asset (.md with front matter)")
    parser.add_argument("--pack", help="Context pack .json produced by build_context.py")
    parser.add_argument("--library", help="Library path (rebuilds the pack from the asset's front matter)")
    parser.add_argument("--revalidate", action="store_true", help="Flag approved assets whose claims changed")
    parser.add_argument("--text", help="Any text file to check against --banned lists")
    parser.add_argument("--banned", action="append", default=[], help="Term list file (repeatable)")
    parser.add_argument("--json", action="store_true", help="Machine-readable output")
    return parser


def main(argv: list[str] | None = None) -> int:
    mnc.configure_stdio()
    args = build_parser().parse_args(argv)
    lib = Path(args.library).resolve() if args.library else None
    if lib is not None and not lib.is_dir():
        mnc.eprint(f"error: library not found: {lib}")
        return 2

    if args.text:
        if not args.banned:
            mnc.eprint("error: --text needs at least one --banned list")
            return 2
        report = check_text(Path(args.text), [Path(p) for p in args.banned])
        title = args.text
    elif args.revalidate:
        if lib is None:
            mnc.eprint("error: --revalidate needs --library")
            return 2
        report = revalidate(lib)
        title = f"revalidate {lib.name}"
    elif args.copy:
        copy_path = Path(args.copy)
        if not copy_path.exists():
            mnc.eprint(f"error: copy file not found: {copy_path}")
            return 2
        pack = mnc.read_json(args.pack) if args.pack else None
        report = validate_file(copy_path, pack, lib)
        title = copy_path.name
    else:
        build_parser().print_help()
        return 2

    if args.json:
        print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
    else:
        print(report.render(title), end="")
    return 0 if report.passed else 1


if __name__ == "__main__":
    sys.exit(main())
