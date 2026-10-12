# Alignment Audit (Rules 85-100 / 16 items) — changelog-semantic-lint

| # | Check | Status | Evidence |
|---|-------|--------|----------|
| 1 | Safety/Ethics section | N/A | Documentation linter; no security research content; Limits covers padding/filler misuse honestly. |
| 2 | Privacy/keys | PASS | No keys/tokens/real names; example URLs use example.test; zero network. |
| 3 | Copyright boundary | PASS | Anchors referenced factually (name, stars as of 2026-10-11, one-layer difference); no anchor text copied; MIT LICENSE shipped. |
| 4 | Fact-check numbers | PASS | 41/41 checks measured, repro command given; parser-tolerance claims marked [estimated]. |
| 5 | Confidence grading | PASS | README: High (85%) rule coverage, Medium (55%) parser tolerance, each with basis sentence. |
| 6 | Minimal Fallback | PASS | "Minimal Fallback (PLAN B)": three grep/date one-liners for the top rules; JSON finding schema is the contract. |
| 7 | Quickstart timing | PASS | Quickstart labelled ~2 min, staged (self-test → own changelog → JSON). |
| 8 | Conflict arbitration | PASS | "Design Trade-offs": false-alarm avoidance > rule completeness > style enforcement, with named rejections (loose prerelease precedence, case-insensitive categories). |
| 9 | Changelog ≥2 iterations | PASS | v0.1.0 → v0.1.1: R001 title-tightening, 3 wrong test expectations fixed, 40→41 tests; this very file is lint-shaped. |
| 10 | Exemption (session rule) | N/A | Session-level governance item; static repo not applicable. |
| 11 | Knowledge cutoff | PASS | Anchor landscape and semver-precedence stance dated "as of 2026-10-11". |
| 12 | Explicit assumptions | PASS | `[Core Assumptions]` lists 4 premises (Keep-a-Changelog grammar, newest-first invariant, Gregorian date strings, six-category vocabulary). |
| 13 | Three-part self-test | PASS | functional (16) + error paths (10) + extreme edges (15) = 41/41 PASS. |
| 14 | Socratic FAQ | PASS | "When NOT to use this?" — generated changelogs, non-KaC formats, accuracy out of reach. |
| 15 | Pareto iteration | PASS | Round 2: correctness dimension (R001 was a no-op rule; now discriminating) + expectation fixes; CHANGELOG-traceable. |
| 16 | ≤60-word opening | PASS | First paragraph is 57 words ending with a judgment sentence ("fail the build, not your release notes' credibility"). |

Additional: **Second-order effects** — "Limits & Second-order Effects" covers heading-parser blind spots, multi-track release orderings, --as-of pinning necessity, and filler-bullet gaming.
