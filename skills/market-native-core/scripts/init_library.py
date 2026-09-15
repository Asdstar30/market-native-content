#!/usr/bin/env python3
"""Scaffold a market content library inside a project.

Copies the skill's `templates/library/` into `<project>/<dir-name>/`, creates one
`markets/<locale>/` folder per requested locale, writes `locales.json`, and adds a
short block to the project's `CLAUDE.md` and `AGENTS.md` (if they exist) that points
future writing sessions at the library. Never overwrites an existing file.

Example:
    python init_library.py --project . --locales en-us,de-de --name "Maple Dental"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import mnc_common as mnc

MARKER_START = "<!-- market-native-core:start -->"
MARKER_END = "<!-- market-native-core:end -->"

INSTRUCTION_BLOCK = """{start}
## Market-native content

Before writing or editing any customer-facing text for this project, read
`{lib}/PROJECT-INSTRUCTIONS.md` and generate a context pack for the exact locale,
channel, page and audience. Write from the pack only. Never translate another locale's
copy. Never state a claim that is not in the pack. Run `validate_copy.py` before showing
copy. If the pack reports missing or stale data, say so instead of writing around it.
{end}
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", required=True, help="Project root that will contain the library")
    parser.add_argument("--locales", default="", help="Comma-separated locale ids, e.g. en-us,de-de")
    parser.add_argument("--name", default="Untitled project", help="Project or company name for placeholders")
    parser.add_argument("--dir-name", default="market-content-library", help="Library folder name")
    parser.add_argument("--no-instructions", action="store_true", help="Do not touch CLAUDE.md / AGENTS.md")
    return parser


def copy_template(src: Path, dst: Path, replacements: dict[str, str], report: list[str]) -> None:
    for item in sorted(src.rglob("*")):
        rel = item.relative_to(src)
        if "_template" in rel.parts:
            continue
        target = dst / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        if target.exists():
            report.append(f"skip (exists)  {rel.as_posix()}")
            continue
        text = mnc.read_text(item)
        for key, value in replacements.items():
            text = text.replace(key, value)
        mnc.write_text(target, text)
        report.append(f"create         {rel.as_posix()}")


def create_market(template_dir: Path, markets_dir: Path, locale: str, report: list[str]) -> None:
    target = markets_dir / locale
    for item in sorted(template_dir.iterdir()):
        dest = target / item.name
        if dest.exists():
            report.append(f"skip (exists)  markets/{locale}/{item.name}")
            continue
        text = mnc.read_text(item).replace("__LOCALE__", locale)
        mnc.write_text(dest, text)
        report.append(f"create         markets/{locale}/{item.name}")
    lang = mnc.language_of(locale)
    seed = mnc.skill_root() / "references" / "banned" / f"generic-{lang}.txt"
    banned = target / "banned.txt"
    if seed.exists() and banned.exists() and not mnc.load_term_list(banned):
        seeded = mnc.read_text(banned).rstrip() + "\n\n# Seeded from generic-" + lang + ".txt\n"
        seeded += "\n".join(mnc.load_term_list(seed)) + "\n"
        mnc.write_text(banned, seeded)
        report.append(f"seed           markets/{locale}/banned.txt from generic-{lang}.txt")


def write_locales(lib: Path, locales: list[str], report: list[str]) -> None:
    path = lib / "locales.json"
    data = mnc.read_json(path) if path.exists() else {"locales": []}
    known = {entry.get("id") for entry in data.get("locales", [])}
    for locale in locales:
        if locale in known:
            continue
        data["locales"].append(
            {
                "id": locale,
                "language": mnc.language_of(locale),
                "market": locale.split("-", 1)[1].upper(),
                "jurisdiction": locale.split("-", 1)[1].upper(),
                "primary_language_for_buyers": True,
                "search_engine": "",
                "default_cta": "",
                "audience_notes": "",
                "stale_after_days": 180,
                "status": "draft",
            }
        )
        report.append(f"add locale     {locale}")
    mnc.write_json(path, data)


def inject_instructions(project: Path, dir_name: str, report: list[str]) -> None:
    block = INSTRUCTION_BLOCK.format(start=MARKER_START, end=MARKER_END, lib=dir_name)
    touched = False
    for name in ("CLAUDE.md", "AGENTS.md"):
        path = project / name
        if not path.exists():
            continue
        text = mnc.read_text(path)
        if MARKER_START in text:
            report.append(f"skip (present) {name}")
            touched = True
            continue
        mnc.write_text(path, text.rstrip() + "\n\n" + block)
        report.append(f"append         {name}")
        touched = True
    if not touched:
        report.append("note           no CLAUDE.md or AGENTS.md found; add this block to your agent instructions:")
        report.append(block)


def main(argv: list[str] | None = None) -> int:
    mnc.configure_stdio()
    args = build_parser().parse_args(argv)
    project = Path(args.project).resolve()
    if not project.is_dir():
        mnc.eprint(f"error: project folder not found: {project}")
        return 2
    locales = [item.strip() for item in args.locales.split(",") if item.strip()]
    bad = [item for item in locales if not mnc.is_locale_id(item)]
    if bad:
        mnc.eprint(f"error: locale ids must be language-market (e.g. en-us), got: {', '.join(bad)}")
        return 2

    template_root = mnc.skill_root() / "templates" / "library"
    lib = project / args.dir_name
    report: list[str] = []
    copy_template(template_root, lib, {"__PROJECT_NAME__": args.name}, report)
    (lib / "packs").mkdir(exist_ok=True)
    for locale in locales:
        create_market(template_root / "markets" / "_template", lib / "markets", locale, report)
    write_locales(lib, locales, report)
    if not args.no_instructions:
        inject_instructions(project, args.dir_name, report)

    print(f"library: {lib}")
    for line in report:
        print(line)
    print("next: fill core/company.json, core/claims.json and markets/<locale>/ (build mode)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
