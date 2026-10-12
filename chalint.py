"""changelog-semantic-lint: Keep-a-Changelog structure + semver monotonicity
+ calendar-date validity for CHANGELOG.md files.

Rules:
  R001 error  missing `# Changelog` H1 title
  R002 error  release heading not `## [version] - YYYY-MM-DD` (Unreleased may omit date)
  R003 error  version is not X.Y.Z (optionally with -prerelease)
  R004 error  date is not a real calendar date
  R005 error  versions not in strictly descending order (newest first)
  R006 error  duplicate version heading
  R007 warn   release contains no standard category (Added/Changed/Fixed/Removed/Deprecated/Security/Unreleased)
  R008 error  standard category heading with no bullet items
  R009 warn   release dated after the as-of date (future-dated)
  R010 warn   no Unreleased section at all
Verdict: PASS / WARN / FAIL.  Exit: 0 / 0 / 1 (2 = usage).
"""
from __future__ import annotations

import os
import re
from datetime import date, datetime

CATEGORIES = ("added", "changed", "fixed", "removed", "deprecated", "security")
VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:-[0-9A-Za-z.-]+)?$")
H1_RE = re.compile(r"^#\s+")
H2_RE = re.compile(r"^##\s+\[([^\]]+)\](?:\s+-\s+(\S+))?\s*$")
H3_RE = re.compile(r"^###\s+(.+?)\s*$")
BULLET_RE = re.compile(r"^\s*[-*]\s+")


def parse_changelog(text: str) -> dict:
    text = text.replace("\r\n", "\n")
    lines = text.split("\n")
    title = None
    releases = []
    cur = None
    cur_cat = None
    for i, line in enumerate(lines, 1):
        if H1_RE.match(line) and title is None and not line.startswith("##"):
            title = re.sub(r"^#\s+", "", line).strip()
            continue
        m = H2_RE.match(line)
        if m:
            cur = {"version": m.group(1).strip(), "date": m.group(2),
                   "line": i, "categories": {}, "order": len(releases)}
            cur_cat = None
            releases.append(cur)
            continue
        m = H3_RE.match(line)
        if m and cur is not None:
            cur_cat = m.group(1).strip()
            cur["categories"].setdefault(cur_cat, [])
            continue
        if BULLET_RE.match(line) and cur is not None and cur_cat is not None:
            cur["categories"][cur_cat].append(re.sub(BULLET_RE, "", line).strip())
    return {"title": title, "releases": releases}


def _version_key(v: str):
    m = VERSION_RE.match(v)
    if not m:
        return None
    return tuple(int(x) for x in m.groups()[:3])


def lint(text: str, as_of: str = None) -> list:
    findings = []
    parsed = parse_changelog(text)

    if parsed["title"] is None or parsed["title"].strip().lower() != "changelog":
        findings.append({"code": "R001", "severity": "error", "line": 1,
                         "message": "missing or mis-titled `# Changelog` H1 (found: %r)" % parsed["title"]})

    as_of_date = datetime.strptime(as_of, "%Y-%m-%d").date() if as_of else None

    prev_key = None
    seen = set()
    has_unreleased = False
    for rel in parsed["releases"]:
        v, d = rel["version"], rel["date"]
        where = "release [%s]" % v
        if v.lower() == "unreleased":
            has_unreleased = True
            if d:
                findings.append({"code": "R002", "severity": "error", "line": rel["line"],
                                 "message": "%s: Unreleased must not carry a date" % where})
        else:
            if not VERSION_RE.match(v):
                findings.append({"code": "R003", "severity": "error", "line": rel["line"],
                                 "message": "%s: version '%s' is not X.Y.Z[-prerelease]" % (where, v)})
            if not d:
                findings.append({"code": "R002", "severity": "error", "line": rel["line"],
                                 "message": "%s: release heading missing ' - YYYY-MM-DD'" % where})
            else:
                try:
                    dd = datetime.strptime(d, "%Y-%m-%d").date()
                    if as_of_date and dd > as_of_date:
                        findings.append({"code": "R009", "severity": "warn", "line": rel["line"],
                                         "message": "%s: date %s is in the future (as-of %s)" % (where, d, as_of)})
                except ValueError:
                    findings.append({"code": "R004", "severity": "error", "line": rel["line"],
                                     "message": "%s: '%s' is not a real calendar date" % (where, d)})
            if v in seen:
                findings.append({"code": "R006", "severity": "error", "line": rel["line"],
                                 "message": "%s: duplicate version" % where})
            seen.add(v)
            vk = _version_key(v)
            if vk and prev_key and vk >= prev_key:
                findings.append({"code": "R005", "severity": "error", "line": rel["line"],
                                 "message": "%s: not strictly descending (newest first)" % where})
            prev_key = vk or prev_key

        if not rel["categories"]:
            findings.append({"code": "R007", "severity": "warn", "line": rel["line"],
                             "message": "%s: no category sections at all" % where})
        for cat, items in rel["categories"].items():
            if cat.lower() in CATEGORIES:
                if not items:
                    findings.append({"code": "R008", "severity": "error", "line": rel["line"],
                                     "message": "%s: category '%s' has no bullet items" % (where, cat)})
            else:
                findings.append({"code": "R007", "severity": "warn", "line": rel["line"],
                                 "message": "%s: non-standard category '%s'" % (where, cat)})

    if parsed["releases"] and not has_unreleased:
        findings.append({"code": "R010", "severity": "warn", "line": 1,
                         "message": "no [Unreleased] section"})
    findings.sort(key=lambda f: (f["severity"] != "error", f["line"]))
    return findings


def verdict(findings: list) -> str:
    if any(f["severity"] == "error" for f in findings):
        return "FAIL"
    if findings:
        return "WARN"
    return "PASS"


def lint_file(path: str, as_of: str = None) -> dict:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        findings = lint(f.read(), as_of)
    return {"path": path, "verdict": verdict(findings), "findings": findings}
