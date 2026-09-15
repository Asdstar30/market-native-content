#!/usr/bin/env python3
"""Generate a context pack for one writing task from a market content library.

The pack is the only input the writing model reads. It is filtered by fixed selectors
(locale, channel, page, audience, optional product and concepts) so the model never
decides what to read, and it reports what is missing or stale instead of leaving gaps
to be filled from memory.

Writes `<library>/packs/<pack_id>.md` (for the model) and `.json` (for validate_copy.py).

Example:
    python build_context.py --library market-content-library --locale en-us \
        --channel web --page product --audience patient --product-id clear-aligners
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from datetime import timedelta
from pathlib import Path
from typing import Any

import mnc_common as mnc

MAX_TERMS = 40
EXPIRY_WARNING_DAYS = 30


class LibraryError(Exception):
    """Raised when the library is missing something the pack cannot do without."""


def load_optional_json(path: Path, default: Any) -> Any:
    return mnc.read_json(path) if path.exists() else default


def load_optional_text(path: Path) -> str:
    return mnc.read_text(path).strip() if path.exists() else ""


def matches(values: Any, wanted: str) -> bool:
    """Empty list or '*' means 'applies to all'."""
    if not values:
        return True
    return "*" in values or wanted in values


def intersects(values: Any, wanted: list[str]) -> bool:
    if not wanted:
        return True
    return bool(set(values or []) & set(wanted))


def find_locale(lib: Path, locale_id: str) -> dict[str, Any]:
    data = load_optional_json(lib / "locales.json", {"locales": []})
    for entry in data.get("locales", []):
        if entry.get("id") == locale_id:
            return entry
    known = ", ".join(sorted(e.get("id", "?") for e in data.get("locales", []))) or "none"
    raise LibraryError(f"locale '{locale_id}' not in locales.json (known: {known})")


def select_claims(claims: list[dict[str, Any]], sel: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    eligible: list[dict[str, Any]] = []
    excluded: dict[str, int] = {}
    today = mnc.today()
    for claim in claims:
        reason = ""
        expires = mnc.parse_date(claim.get("expires"))
        if claim.get("status") != "verified":
            reason = f"status={claim.get('status', 'missing')}"
        elif expires and expires < today:
            reason = "expired"
        elif not matches(claim.get("eligible_markets"), sel["locale"]):
            reason = "not eligible for locale"
        elif not matches(claim.get("eligible_channels"), sel["channel"]):
            reason = "not eligible for channel"
        elif sel["product_id"] and not matches(claim.get("product_ids"), sel["product_id"]):
            reason = "other product"
        elif not matches(claim.get("audiences"), sel["audience"]):
            reason = "other audience"
        elif not intersects(claim.get("tags"), sel["concepts"]):
            reason = "other concept"
        if reason:
            excluded[reason] = excluded.get(reason, 0) + 1
        else:
            eligible.append(claim)
    return eligible, excluded


def select_terms(glossary: dict[str, Any], sel: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    required: list[dict[str, Any]] = []
    draft_ok: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    forbidden: list[str] = []
    for term in glossary.get("terms", []):
        forbidden.extend(term.get("alternatives_to_avoid") or [])
        status = term.get("status")
        kind = term.get("term_type", "commercial")
        if status == "rejected":
            forbidden.append(term.get("term", ""))
            continue
        relevant = intersects(term.get("tags"), sel["concepts"]) and (
            not sel["product_id"] or matches(term.get("product_ids"), sel["product_id"])
        )
        if status == "approved":
            if relevant:
                required.append(term)
        elif status in ("pending_review", "draft"):
            if kind in ("technical", "regulatory"):
                blocked.append(term)
            elif relevant:
                draft_ok.append(term)
    if len(required) > MAX_TERMS:
        required = required[:MAX_TERMS]
    return {"required": required, "draft_ok": draft_ok, "blocked": blocked, "forbidden": [f for f in forbidden if f]}


def select_objections(data: dict[str, Any], sel: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        obj
        for obj in data.get("objections", [])
        if matches(obj.get("audiences"), sel["audience"]) and intersects(obj.get("tags"), sel["concepts"])
    ]


def competitor_summary(data: dict[str, Any], stale_after: int) -> dict[str, Any]:
    entries = data.get("competitors", [])
    dates = [d for d in (mnc.parse_date(e.get("retrieved_at")) for e in entries) if d]
    oldest = min(dates).isoformat() if dates else ""
    newest = max(dates).isoformat() if dates else ""
    stale = bool(dates) and (mnc.today() - min(dates)).days > stale_after
    orders: dict[str, int] = {}
    for entry in entries:
        key = " > ".join(entry.get("section_order") or [])
        if key:
            orders[key] = orders.get(key, 0) + 1
    common_order = max(orders, key=orders.get) if orders else ""
    return {
        "count": len(entries),
        "oldest": oldest,
        "newest": newest,
        "stale": stale,
        "common_section_order": common_order,
        "gaps": [e.get("gaps", "") for e in entries if e.get("gaps")],
        "hero_lines": [e.get("hero", {}).get("h1", "") for e in entries if e.get("hero", {}).get("h1")],
        "proof_used": mnc.dedupe([p for e in entries for p in (e.get("proof_used") or [])]),
    }


def build(lib: Path, sel: dict[str, Any]) -> dict[str, Any]:
    locale = find_locale(lib, sel["locale"])
    market_dir = lib / "markets" / sel["locale"]
    if not market_dir.is_dir():
        raise LibraryError(f"markets/{sel['locale']}/ does not exist; run init_library.py --locales {sel['locale']}")
    warnings: list[str] = []
    lang = mnc.language_of(sel["locale"])

    company = load_optional_json(lib / "core" / "company.json", {})
    products = load_optional_json(lib / "core" / "products.json", {"products": []})
    claims_data = load_optional_json(lib / "core" / "claims.json", {"claims": []})
    brand = load_optional_text(lib / "core" / "brand.md")
    glossary = load_optional_json(market_dir / "glossary.json", {"terms": []})
    objections = load_optional_json(market_dir / "objections.json", {"objections": []})
    voice = load_optional_text(market_dir / "voice.md")
    competitors = load_optional_json(market_dir / "competitors.json", {"competitors": []})
    limits_all = load_optional_json(lib / "channels" / sel["channel"] / "limits.json", {})
    limits = dict(limits_all.get("default", {}))
    limits.update(limits_all.get(sel["locale"], {}))
    blueprint_override = lib / "channels" / sel["channel"] / "blueprints" / f"{sel['page']}.md"

    product = next((p for p in products.get("products", []) if p.get("product_id") == sel["product_id"]), None)
    if sel["product_id"] and product is None:
        warnings.append(f"product_id '{sel['product_id']}' not found in core/products.json")

    claims, excluded = select_claims(claims_data.get("claims", []), sel)
    if not claims:
        warnings.append("no eligible claims: the writer has nothing provable to say for this selection")
    soon = mnc.today() + timedelta(days=EXPIRY_WARNING_DAYS)
    for claim in claims:
        expires = mnc.parse_date(claim.get("expires"))
        if expires and expires <= soon:
            warnings.append(f"claim {claim.get('claim_id')} expires {expires.isoformat()}")

    terms = select_terms(glossary, sel)
    if not terms["required"]:
        warnings.append("no approved glossary terms for this selection (gate 2 not done?)")
    banned_market = mnc.load_term_list(market_dir / "banned.txt")
    banned_generic = mnc.load_term_list(mnc.skill_root() / "references" / "banned" / f"generic-{lang}.txt")
    forbidden = mnc.dedupe(banned_market + terms["forbidden"] + banned_generic)
    blocked_terms = [t.get("term", "") for t in terms["blocked"] if t.get("term")]

    objs = select_objections(objections, sel)
    if not objs:
        warnings.append("no objections recorded for this audience")
    if not voice:
        warnings.append(f"markets/{sel['locale']}/voice.md is empty")
    if not brand or "| We say" not in brand or brand.count("|") < 12:
        warnings.append("core/brand.md has no differentiation rows; copy will be average by construction")
    comp = competitor_summary(competitors, int(locale.get("stale_after_days", 180) or 180))
    if comp["count"] == 0:
        warnings.append("no competitor signals for this locale")
    elif comp["stale"]:
        warnings.append(f"competitor signals oldest {comp['oldest']} exceed stale_after_days; refresh")
    if not limits:
        warnings.append(f"channels/{sel['channel']}/limits.json missing; no length checks will run")

    fingerprint = hashlib.sha256(
        "|".join(
            [sel["locale"], sel["channel"], sel["page"], sel["audience"], sel["product_id"], ",".join(sel["concepts"])]
            + sorted(c.get("claim_id", "") for c in claims)
            + sorted(t.get("term", "") for t in terms["required"])
        ).encode("utf-8")
    ).hexdigest()[:8]
    pack_id = f"cp-{mnc.today().strftime('%Y%m%d')}-{sel['locale']}-{sel['channel']}-{sel['page']}-{fingerprint}"

    return {
        "pack_id": pack_id,
        "generated_at": mnc.today().isoformat(),
        "selectors": sel,
        "locale": locale,
        "company": {"name": company.get("name", ""), "one_line": company.get("one_line", ""), "status": company.get("status", "")},
        "product": product,
        "brand": brand,
        "claims": claims,
        "claims_excluded": excluded,
        "required_terms": terms["required"],
        "draft_terms": terms["draft_ok"],
        "blocked_terms": blocked_terms,
        "forbidden_terms": forbidden,
        "objections": objs,
        "voice": voice,
        "limits": limits,
        "blueprint": sel["page"],
        "blueprint_override": mnc.read_text(blueprint_override) if blueprint_override.exists() else "",
        "competitors": comp,
        "warnings": warnings,
    }


def render(pack: dict[str, Any]) -> str:
    sel = pack["selectors"]
    loc = pack["locale"]
    lines: list[str] = []
    add = lines.append
    add(f"# Context pack {pack['pack_id']}")
    add("")
    add("Write from this pack only. Do not read the library directly, do not translate another")
    add("locale, do not state anything that is not a claim below. Run validate_copy.py when done.")
    add("")
    add("## Identity")
    add(f"- locale: {sel['locale']} (jurisdiction {loc.get('jurisdiction', '?')}, primary language for buyers: {loc.get('primary_language_for_buyers', '?')})")
    add(f"- channel: {sel['channel']} | page: {sel['page']} | audience: {sel['audience']}")
    if sel["product_id"]:
        add(f"- product: {sel['product_id']}")
    if sel["concepts"]:
        add(f"- concepts: {', '.join(sel['concepts'])}")
    if sel["intent"]:
        add(f"- intent: {sel['intent']}")
    add(f"- default conversion action in this market: {loc.get('default_cta') or 'not set'}")
    if loc.get("audience_notes"):
        add(f"- audience notes: {loc['audience_notes']}")
    add("")
    add("## Company")
    add(f"{pack['company'].get('name', '')}: {pack['company'].get('one_line', '')}".strip(": "))
    if pack["product"]:
        names = pack["product"].get("name", {})
        add(f"Product {pack['product'].get('product_id')}: {', '.join(f'{k}={v}' for k, v in names.items())}")
    if pack["brand"]:
        add("")
        add("### Brand and differentiation")
        add(pack["brand"])
    add("")
    add("## Eligible claims (the only things you may promise)")
    if not pack["claims"]:
        add("(none)")
    for claim in pack["claims"]:
        add(f"- [{claim.get('claim_id')}] {claim.get('statement')}")
        add(f"  evidence: {claim.get('evidence', '')} | expires: {claim.get('expires', '?')}")
    if pack["claims_excluded"]:
        add(f"Excluded: " + "; ".join(f"{n} {r}" for r, n in sorted(pack["claims_excluded"].items())))
    add("")
    add("## Required terms (approved; use these, not synonyms)")
    if not pack["required_terms"]:
        add("(none approved yet)")
    for term in pack["required_terms"]:
        extra = f" | search: {term['search_term']}" if term.get("search_term") and term["search_term"] != term.get("term") else ""
        add(f"- {term.get('term')} ({term.get('concept_id')}, {term.get('term_type')}){extra}")
        if term.get("usage_example"):
            add(f"  e.g. {term['usage_example']}")
    if pack["draft_terms"]:
        add("")
        add("Draft commercial terms (usable, will be flagged for review):")
        for term in pack["draft_terms"]:
            add(f"- {term.get('term')} ({term.get('concept_id')})")
    if pack["blocked_terms"]:
        add("")
        add("Blocked technical/regulatory terms awaiting approval. Do not use and do not invent a substitute; say the term is pending:")
        for term in pack["blocked_terms"]:
            add(f"- {term}")
    add("")
    add("## Forbidden terms")
    add(", ".join(pack["forbidden_terms"]) if pack["forbidden_terms"] else "(none)")
    add("")
    add("## Buyer objections to answer")
    if not pack["objections"]:
        add("(none recorded)")
    for obj in pack["objections"]:
        add(f"- {obj.get('statement')}")
        if obj.get("buyer_words"):
            add(f"  buyer words: {' / '.join(obj['buyer_words'])}")
        if obj.get("answer_claim_refs"):
            add(f"  answered by: {', '.join(obj['answer_claim_refs'])}")
    add("")
    add("## Voice")
    add(pack["voice"] or "(voice.md is empty)")
    add("")
    add("## Limits (characters per field)")
    add(", ".join(f"{k} <= {v}" for k, v in sorted(pack["limits"].items())) if pack["limits"] else "(none)")
    add("")
    add(f"## Blueprint: {pack['blueprint']}")
    add(pack["blueprint_override"] or f"Use the adapter skill's blueprint for '{pack['blueprint']}'.")
    add("")
    add("## Competitor pattern")
    comp = pack["competitors"]
    add(f"- {comp['count']} competitors, retrieved {comp['oldest']} to {comp['newest']}{' (STALE)' if comp['stale'] else ''}")
    if comp["common_section_order"]:
        add(f"- most common section order: {comp['common_section_order']}")
    if comp["proof_used"]:
        add(f"- proof they use: {', '.join(comp['proof_used'])}")
    if comp["hero_lines"]:
        add("- their hero lines (vocabulary and structure only; never the message):")
        lines.extend(f"  - {h}" for h in comp["hero_lines"])
    if comp["gaps"]:
        add("- gaps to exploit:")
        lines.extend(f"  - {g}" for g in comp["gaps"])
    add("")
    add("## Warnings")
    if not pack["warnings"]:
        add("(none)")
    lines.extend(f"- {w}" for w in pack["warnings"])
    add("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--library", required=True, help="Path to the market content library")
    parser.add_argument("--locale", required=True, help="language-market id, e.g. en-us")
    parser.add_argument("--channel", required=True, help="web | app | document | email | slide")
    parser.add_argument("--page", required=True, help="Blueprint name, e.g. product, home")
    parser.add_argument("--audience", required=True, help="audience_id from core/company.json")
    parser.add_argument("--product-id", default="", help="product_id from core/products.json")
    parser.add_argument("--concepts", default="", help="Comma-separated tags to narrow terms, claims, objections")
    parser.add_argument("--intent", default="", help="Free-text intent stored in the pack")
    parser.add_argument("--out-dir", default="", help="Defaults to <library>/packs")
    parser.add_argument("--stdout", action="store_true", help="Print the markdown pack instead of the summary")
    return parser


def selectors_from_args(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "locale": args.locale,
        "channel": args.channel,
        "page": args.page,
        "audience": args.audience,
        "product_id": args.product_id,
        "concepts": [c.strip() for c in args.concepts.split(",") if c.strip()],
        "intent": args.intent,
    }


def main(argv: list[str] | None = None) -> int:
    mnc.configure_stdio()
    args = build_parser().parse_args(argv)
    if not mnc.is_locale_id(args.locale):
        mnc.eprint(f"error: locale must be language-market (e.g. en-us), got '{args.locale}'")
        return 2
    lib = Path(args.library).resolve()
    if not lib.is_dir():
        mnc.eprint(f"error: library not found: {lib}")
        return 2
    try:
        pack = build(lib, selectors_from_args(args))
    except LibraryError as exc:
        mnc.eprint(f"error: {exc}")
        return 1
    markdown = render(pack)
    out_dir = Path(args.out_dir) if args.out_dir else lib / "packs"
    mnc.write_text(out_dir / f"{pack['pack_id']}.md", markdown)
    mnc.write_json(out_dir / f"{pack['pack_id']}.json", pack)
    if args.stdout:
        print(markdown)
    else:
        print(f"pack: {out_dir / (pack['pack_id'] + '.md')}")
        print(f"claims: {len(pack['claims'])} | terms: {len(pack['required_terms'])} | objections: {len(pack['objections'])} | forbidden: {len(pack['forbidden_terms'])}")
        print(f"approx tokens: {mnc.approx_tokens(markdown)}")
        for warning in pack["warnings"]:
            print(f"warning: {warning}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
