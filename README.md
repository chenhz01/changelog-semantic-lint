# changelog-semantic-lint

A validator for CHANGELOG.md files that enforces three things humans keep getting wrong: Keep-a-Changelog structure (title, `## [version] - date` headings, standard categories with bullets), strictly descending semver order, and *real* calendar dates — February 30th and leap-day slips fail the build, not your release notes' credibility. Ten rule codes, zero dependencies, one command.

**Confidence: High (85%)** that the ten rules catch the structural defects that actually mislead changelog readers; **Medium (55%)** that regex-based structure parsing survives your house style (nested lists, footers, link references) — the parser is deliberately tolerant, but exotic layouts may need rule relaxation [estimated].

<p align="center"><img src="docs/demo.gif" alt="demo" width="720"></p>

## Problem

Changelogs are read more than tested, so they rot silently: versions listed in random order, duplicate `## [1.2.0]` headings from a bad rebase, `2026-02-30` dates that no calendar ever had, `### Fixed` sections with nothing under them. Existing tooling mostly lints *commit messages*: gajus/conventional-changelog-lint-config-canonical (5★ as of 2026-10-11) is a shareable config for conventional-changelog-lint, HikawaRin/commitlint-config-megengine (0★) is another commit-convention config, and aanatoly/changelog-tool (0★) lints against the single-release Common Changelog style — all operate one level below the artifact users actually read. The overlooked angle: the CHANGELOG file itself has a checkable grammar, and three of its rules (monotonic versions, real dates, category hygiene) are mechanically enforceable.

## How it works

The parser walks headings — `#` title, `## [version] - date` releases, `### category` sections, `- ` bullets — and runs ten rules:

| Code | Sev | Rule |
|---|---|---|
| R001 | error | H1 must be `# Changelog` (case-insensitive) |
| R002 | error | heading must be `## [X.Y.Z] - YYYY-MM-DD`; `[Unreleased]` may omit the date |
| R003 | error | version is not `X.Y.Z` (optional `-prerelease`) |
| R004 | error | date is not a real calendar date (leap years included) |
| R005 | error | versions not strictly descending (newest first) |
| R006 | error | duplicate version heading |
| R007 | warn | release with no standard category, or non-standard category name |
| R008 | error | standard category heading with no bullets |
| R009 | warn | release dated after the `--as-of` reference date |
| R010 | warn | no `[Unreleased]` section |

Verdict FAIL / WARN / PASS; exit 1 only on FAIL. Lowercase categories are accepted; trailing `[1.0.0]: https://…` link-reference footers are ignored.

## Quickstart (~2 min)

```bash
# 1. Self-test: 41 checks, functional / error-path / extreme-edge (~1 s)
python self_test.py

# 2. Lint your changelog
python cli.py CHANGELOG.md                      # human-readable findings
python cli.py CHANGELOG.md --as-of 2026-10-11   # future-date warnings anchored to today
python cli.py CHANGELOG.md --json > report.json
```

## Why not X

| Alternative | Why not |
|---|---|
| conventional-changelog-lint configs (gajus/…canonical 5★, HikawaRin/…megengine 0★) | Lint commit *messages* that later generate changelogs; the generated file itself is never re-validated, and manual edits bypass them entirely |
| aanatoly/changelog-tool (0★) | Enforces the single-release Common Changelog style — a different spec; no version monotonicity or calendar-date validation |
| markdownlint | Generic markdown hygiene (line length, heading increments); knows nothing about `[version]` semantics, semver order, or date validity |
| keep-a-changelog GitHub actions | Assume well-formed input and extract data; few fail on R004/R005-class defects |

## Minimal Fallback (PLAN B)

No Python? The three highest-value rules are one grep each: real dates (`grep -nE '\[[0-9]+\.[0-9]+\.[0-9]+\] - [0-9]{4}-[0-9]{2}-[0-9]{2}'` plus a `date -d` loop), duplicate versions (`grep -o '^\## \[[^]]*\]' | sort | uniq -d`), and category-without-bullets (eyeball — or any 20-line script). The JSON finding schema (`{code, severity, line, message}`) is the contract a re-implementation must emit.

## Design Trade-offs

Priority order: **false-alarm avoidance > rule completeness > style enforcement**. Versions compare as `(major, minor, patch)` integer tuples — `1.10.0 > 1.9.0` is handled, but pre-release ordering follows semver *loosely* (`2.0.0-rc.1` sorts as `2.0.0`; full semver precedence between prereleases is deliberately not implemented). Categories are case-insensitive and only the six standard names are recognized; anything else warns instead of fails, because teams legitimately add `### Performance`. Structure parsing is heading-based, so HTML comments, nested sub-bullets and footer links are tolerated rather than policed. `R010` (missing Unreleased) warns instead of fails since not every repo keeps one.

## Limits & Second-order Effects

- Heading-based parsing means a changelog assembled with `*` releases (`* [1.0.0]`) or indented headings is invisible — tolerance for exotic styles caps at what `H2_RE` sees.
- Strict descending order rejects multi-track changelogs (maintenance branches releasing `1.2.1` after `2.0.0` landed); such repos need per-branch files.
- Future-date warnings only fire if you pass `--as-of`; without it, a changelog dated next year passes — automation should always pin the date.
- If CI enforces R008, authors will pad empty categories with filler bullets ("various improvements") — the lint makes structure, not honesty.

## FAQ

**Does it generate changelogs from commits?** No — the anchors above own that job. This validates the human-editable artifact *after* whatever process produced it.

**Why is a duplicate version an error but a non-standard category only a warning?** Duplicates mislead unambiguously (two artifacts claiming the same identity); a custom category is a style choice readers can adapt to.

**When NOT to use this?** Don't use it on generated changelogs assembled from thousands of commit lines where category rules don't apply; don't use it for single-file release notes that intentionally deviate from Keep-a-Changelog (the linter will fight your format); and don't use it to check changelog *accuracy* — no linter can verify that "Fixed crash" fixed a crash.

**Is full semver precedence supported?** Partially, as of 2026-10-11: `X.Y.Z[-pre]` parsing and monotonic tuple ordering are; prerelease-vs-release precedence subtleties (`1.0.0-rc.1 < 1.0.0 < 1.0.1`) are approximated, not spec-complete.

## [Core Assumptions]

1. The file follows Keep-a-Changelog heading conventions (`#`/`##`/`###`, bracketed versions) — the linter validates that grammar, it does not discover arbitrary formats.
2. Changelogs are append-mostly and newest-first; descending order is the intended invariant.
3. Dates are Gregorian `YYYY-MM-DD` strings whose plausibility (real calendar dates, not in the future) is mechanically checkable.
4. The six standard category names are the shared vocabulary; additional categories deserve visibility, not rejection.

*Data as of 2026-10-11. Measured: 41/41 self-test checks PASS (functional 16, error paths 10, extreme edges 15), repro `python self_test.py` on Windows 10 / CPython 3.11. Parser tolerance for exotic house styles is [estimated].*

---

Part of the [zhengming-toolbox](https://github.com/chenhz01/zhengming-toolbox) — 55 purpose-built AI-engineering tools across neglected niches.

Related tools: [api-contract-drift](https://github.com/chenhz01/api-contract-drift) · [schema-evolution-grader](https://github.com/chenhz01/schema-evolution-grader) · [json-output-salvage](https://github.com/chenhz01/json-output-salvage)
