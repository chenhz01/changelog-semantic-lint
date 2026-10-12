# Changelog

## [0.1.1] - 2026-10-11

### Changed (round-2 iteration after first-draft self-audit)

- **Correctness:** tightened R001 — a file titled `# History` (or anything not "Changelog") previously passed with zero findings because any H1 satisfied the title check; the rule now requires the H1 to *be* "Changelog" (case-insensitive), with the found title echoed in the message.
- **Test rigor:** suite grew 40 → 41 checks and three first-draft expectations were themselves wrong (well-formed changelog without `[Unreleased]` asserted PASS although R010 correctly warns; prerelease monotonicity asserted PASS for the same reason; an orphan `### Added` with no release section was expected to FAIL although the parser correctly ignores it) — all rewritten to assert intended semantics.
- **Docs:** FAQ gained explicit partial-semver-precedence disclosure.

## [0.1.0] - 2026-10-11

### Added

- `chalint.py`: heading-based CHANGELOG parser (title/releases/categories/bullets), 10 rule codes (R001–R010) covering structure, semver monotonicity, calendar-date validity (leap years), duplicates, category hygiene, future dates, missing Unreleased; PASS/WARN/FAIL verdicts.
- `cli.py`: multi-file linting, `--as-of` reference date, `--json`; exit codes 0/1/2.
- `self_test.py`: three families — functional, error paths, extreme edges (200 releases, 100KB bullets, leap-day years, unicode/emoji bullets, CRLF, link-ref footers).
- MIT LICENSE (zhengming contributors), README, initial ALIGNMENT audit.
