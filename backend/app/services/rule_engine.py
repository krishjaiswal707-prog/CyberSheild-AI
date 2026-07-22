"""
Feature 3 — Rule-Based Override Layer

Runs BEFORE the LLM call. If a combination of:
  - Government agency name  +
  - Urgency/threat keyword  +
  - Money/account action keyword
is found in the same input, the risk_score is floored at 90 (CRITICAL).

Design principles:
  - Every rule that fires is logged by name (auditable).
  - Rules are defined as named dictionaries for easy extension.
  - Returns a tuple: (floor_score | None, rule_name | None, matched_flags).
"""
from __future__ import annotations

import re
import logging

logger = logging.getLogger(__name__)

# ── Keyword Sets ───────────────────────────────────────────────────────────────

GOV_AGENCY_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("CBI", re.compile(r"\bCBI\b", re.IGNORECASE)),
    ("ED", re.compile(r"\bED\b|\bEnforcement Directorate\b", re.IGNORECASE)),
    ("Customs", re.compile(r"\bCustoms\b|\bcustom officer\b", re.IGNORECASE)),
    ("Income Tax", re.compile(r"\bIncome.Tax\b|\bIT department\b", re.IGNORECASE)),
    ("Narcotics", re.compile(r"\bNarcotics\b|\bNCB\b", re.IGNORECASE)),
    ("TRAI", re.compile(r"\bTRAI\b", re.IGNORECASE)),
    ("Police", re.compile(r"\bpolice\b|\bpolice officer\b", re.IGNORECASE)),
    ("RBI", re.compile(r"\bRBI\b|\bReserve Bank\b", re.IGNORECASE)),
    ("CID", re.compile(r"\bCID\b", re.IGNORECASE)),
    ("Interpol", re.compile(r"\bInterpol\b", re.IGNORECASE)),
]

URGENCY_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("arrest_threat", re.compile(r"\barrest\b|\barrested\b|\barrest warrant\b", re.IGNORECASE)),
    ("case_registered", re.compile(r"\bcase registered\b|\bcriminal case\b|\bFIR\b", re.IGNORECASE)),
    ("jail_threat", re.compile(r"\bjail\b|\bprison\b|\bimprisonment\b", re.IGNORECASE)),
    ("legal_action", re.compile(r"\blegal action\b|\blegal notice\b|\bcourt order\b", re.IGNORECASE)),
    ("last_warning", re.compile(r"\blast (warning|chance|opportunity)\b", re.IGNORECASE)),
    ("dont_tell_anyone", re.compile(r"\bdon[\'']?t tell\b|\bdo not share\b|\bkeep (it )?confidential\b", re.IGNORECASE)),
    ("digital_arrest", re.compile(r"\bdigital arrest\b", re.IGNORECASE)),
    ("video_call_demand", re.compile(r"\bvideo call\b.{0,60}(CBI|ED|police|officer)", re.IGNORECASE)),
    ("stay_online", re.compile(r"\bstay online\b|\bdon[\'']?t disconnect\b|\bremain on call\b", re.IGNORECASE)),
]

MONEY_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("money_transfer", re.compile(r"\btransfer\b.{0,40}(₹|\bRs\.?\b|\brupee)", re.IGNORECASE)),
    ("bank_account_demand", re.compile(r"\bbank account\b|\baccount number\b|\bIFSC\b", re.IGNORECASE)),
    ("upi_demand", re.compile(r"\bUPI\b|\bGoogle Pay\b|\bPhonePe\b|\bPaytm\b", re.IGNORECASE)),
    ("payment_bail", re.compile(r"\bbail\b.{0,60}(pay|amount|₹)", re.IGNORECASE)),
    ("fine_immediate", re.compile(r"\bfine\b.{0,40}(pay|immediately|now)", re.IGNORECASE)),
    ("send_money", re.compile(r"\b(send|pay|deposit).{0,30}(money|amount|cash|₹)", re.IGNORECASE)),
    ("clear_name", re.compile(r"\bclear your name\b|\bsave yourself\b", re.IGNORECASE)),
]

# Hindi-specific urgency patterns (Devanagari)
HINDI_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("hindi_arrest", re.compile(r"गिरफ्तारी|वारंट|जेल|अरेस्ट", re.IGNORECASE)),
    ("hindi_agency", re.compile(r"सीबीआई|ईडी|पुलिस|कस्टम|आयकर")),
    ("hindi_money", re.compile(r"पैसे|रुपये|ट्रांसफर|जुर्माना")),
]

# ISOLATION tactic — asking to stay on call and not contact anyone
ISOLATION_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("isolation_no_lawyer", re.compile(r"\bdon[\'']?t (call|contact|talk to).{0,30}(lawyer|advocate|family|police)\b", re.IGNORECASE)),
    ("isolation_mute", re.compile(r"\bkeep (this|it).{0,20}(secret|private|confidential)\b", re.IGNORECASE)),
]

# General scam signal patterns (used for fallback scoring, not hard rule triggers)
GENERAL_SCAM_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("urgency_tactic", re.compile(r"\burgent\b|\bimmediately\b|\bright now\b|\bact now\b", re.IGNORECASE)),
    ("fake_kyc", re.compile(r"\bkyc\b|\bupdate.*details\b|\bsuspended.*account\b|\breactivate\b", re.IGNORECASE)),
    ("verify_tactic", re.compile(r"\bclick here\b|\btap now\b|\bverify now\b|\bconfirm now\b", re.IGNORECASE)),
    ("prize_bait", re.compile(r"\bprize\b|\bwon\b|\bwinner\b|\blottery\b|\breward\b", re.IGNORECASE)),
    ("otp_request", re.compile(r"\botp\b|\bone.?time password\b|\bshare.*code\b|\bforward.*code\b", re.IGNORECASE)),
    ("suspicious_link", re.compile(r"http://|bit\.ly|tinyurl|t\.me|wa\.me", re.IGNORECASE)),
    ("account_blocked", re.compile(r"\baccount.*block(ed)?\b|\bblock(ed)?.*account\b", re.IGNORECASE)),
    ("personal_info", re.compile(r"\baadhaar\b|\bpan card\b|\bbank detail\b|\bdebit card\b", re.IGNORECASE)),
    ("processing_fee", re.compile(r"\bprocessing fee\b|\bregistration fee\b|\bsecurity deposit\b", re.IGNORECASE)),
    ("govt_impersonation_generic", re.compile(r"\bofficer\b|\bgovernment\b|\bauthority\b", re.IGNORECASE)),
]


# ── Rule Definitions ───────────────────────────────────────────────────────────

RULES: list[dict] = [
    {
        "name": "RULE_AGENCY_URGENCY_MONEY",
        "description": "Government agency + arrest/legal threat + money demand — classic digital arrest pattern",
        "floor_score": 92,
        "tier": "CRITICAL",
        "check": lambda gov, urg, mon, iso: bool(gov and urg and mon),
    },
    {
        "name": "RULE_AGENCY_URGENCY",
        "description": "Government agency + arrest/legal threat (no explicit money yet — could be early stage)",
        "floor_score": 75,
        "tier": "HIGH",
        "check": lambda gov, urg, mon, iso: bool(gov and urg and not mon),
    },
    {
        "name": "RULE_ISOLATION_WITH_AGENCY",
        "description": "Agency + isolation tactic — a strong scam signal",
        "floor_score": 80,
        "tier": "HIGH",
        "check": lambda gov, urg, mon, iso: bool(gov and iso),
    },
    {
        "name": "RULE_DIGITAL_ARREST_EXPLICIT",
        "description": "Explicit 'digital arrest' phrase — always critical",
        "floor_score": 95,
        "tier": "CRITICAL",
        "check": lambda gov, urg, mon, iso: False,  # handled separately below
    },
]


def _match_group(text: str, patterns: list[tuple[str, re.Pattern]]) -> list[str]:
    """Returns names of patterns that matched."""
    return [name for name, pat in patterns if pat.search(text)]


def fallback_score_from_flags(flags: list[str]) -> int:
    """Compute a 0-100 score from matched signal flags when Claude is unavailable."""
    score = 5
    gov_keywords = {"CBI", "ED", "Customs", "Income Tax", "Narcotics", "TRAI",
                    "Police", "RBI", "CID", "Interpol", "hindi_agency"}
    urgency_keywords = {"arrest_threat", "case_registered", "jail_threat", "legal_action",
                        "last_warning", "dont_tell_anyone", "digital_arrest",
                        "video_call_demand", "stay_online", "hindi_arrest"}
    money_keywords = {"money_transfer", "bank_account_demand", "upi_demand",
                      "payment_bail", "fine_immediate", "send_money",
                      "clear_name", "hindi_money"}
    isolation_keywords = {"isolation_no_lawyer", "isolation_mute"}
    general_keywords = {"urgency_tactic", "fake_kyc", "verify_tactic", "prize_bait",
                        "otp_request", "suspicious_link", "account_blocked",
                        "personal_info", "processing_fee", "govt_impersonation_generic"}

    flag_set = set(flags)
    gov_count = len(flag_set & gov_keywords)
    urg_count = len(flag_set & urgency_keywords)
    mon_count = len(flag_set & money_keywords)
    iso_count = len(flag_set & isolation_keywords)
    gen_count = len(flag_set & general_keywords)

    score += gov_count * 12
    score += urg_count * 10
    score += mon_count * 14
    score += iso_count * 10
    score += gen_count * 8

    if gov_count > 0 and urg_count > 0:
        score += 10
    if gov_count > 0 and mon_count > 0:
        score += 15
    if urg_count > 0 and mon_count > 0:
        score += 10
    if gov_count > 0 and urg_count > 0 and mon_count > 0:
        score += 10

    return min(100, max(0, score))


def run_rule_engine(text: str) -> tuple[int | None, str | None, list[str]]:
    """
    Main entry point for the rule-based override layer.

    Returns:
        (floor_score, rule_name, matched_flags)
        - floor_score: minimum score to enforce (None = no override)
        - rule_name:   name of the rule that fired (None = no override)
        - matched_flags: list of specific flag names that matched
    """
    all_matched_flags: list[str] = []

    # ── Special case: explicit "digital arrest" phrase ─────────────────────────
    digital_arrest_match = re.search(r"\bdigital arrest\b", text, re.IGNORECASE)
    if digital_arrest_match:
        logger.warning("RULE_DIGITAL_ARREST_EXPLICIT fired on input: %.80s...", text)
        return 95, "RULE_DIGITAL_ARREST_EXPLICIT", ["digital_arrest_explicit"]

    # ── Match each group ───────────────────────────────────────────────────────
    gov_matches = _match_group(text, GOV_AGENCY_PATTERNS)
    urg_matches = _match_group(text, URGENCY_PATTERNS)
    mon_matches = _match_group(text, MONEY_PATTERNS)
    iso_matches = _match_group(text, ISOLATION_PATTERNS)
    hin_matches = _match_group(text, HINDI_PATTERNS)
    gen_matches = _match_group(text, GENERAL_SCAM_PATTERNS)

    # Treat Hindi matches as additional signals
    if hin_matches:
        gov_matches += [f"hindi_{m}" for m in hin_matches if "agency" in m]
        urg_matches += [f"hindi_{m}" for m in hin_matches if "arrest" in m]
        mon_matches += [f"hindi_{m}" for m in hin_matches if "money" in m]

    all_matched_flags = gov_matches + urg_matches + mon_matches + iso_matches + gen_matches

    # ── Evaluate rules in priority order ──────────────────────────────────────
    for rule in RULES:
        if rule["name"] == "RULE_DIGITAL_ARREST_EXPLICIT":
            continue  # already handled
        if rule["check"](gov_matches, urg_matches, mon_matches, iso_matches):
            logger.warning(
                "Rule %s fired. gov=%s urg=%s mon=%s iso=%s",
                rule["name"], gov_matches, urg_matches, mon_matches, iso_matches,
            )
            return rule["floor_score"], rule["name"], all_matched_flags

    # No rule fired
    if all_matched_flags:
        logger.info("Rule engine: partial signals found but no rule threshold met: %s", all_matched_flags)

    return None, None, all_matched_flags


def apply_rule_override(
    llm_score: int,
    llm_flags: list[str],
    floor_score: int | None,
    rule_name: str | None,
    rule_flags: list[str],
) -> tuple[int, str, list[str], bool, str | None]:
    """
    Fuses LLM output with rule engine output.
    Rule engine always wins if it fires (takes the maximum of floor_score vs llm_score).

    Returns:
        (final_score, final_tier, final_flags, override_fired, rule_name)
    """
    # Merge flags, dedup
    merged_flags = list(dict.fromkeys(rule_flags + llm_flags))
    override_fired = False

    if floor_score is not None and llm_score < floor_score:
        final_score = floor_score
        override_fired = True
    else:
        final_score = llm_score

    final_tier = _score_to_tier(final_score)
    return final_score, final_tier, merged_flags, override_fired, rule_name


def score_to_tier(score: int) -> str:
    if score >= 85:
        return "CRITICAL"
    if score >= 60:
        return "HIGH"
    if score >= 35:
        return "MEDIUM"
    return "LOW"


_score_to_tier = score_to_tier  # internal alias for backward compat
