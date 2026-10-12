"""Self-test for changelog-semantic-lint: functional / error-path / extreme-edge."""
from __future__ import annotations

import os
import sys
import tempfile

import chalint

_results = []
AS_OF = "2026-10-11"


def record(family, name, ok, detail=""):
    _results.append((family, name, "PASS" if ok else "FAIL", detail))


def codes(findings, code):
    return [f for f in findings if f["code"] == code]


def cl(title="# Changelog", releases=(), footer=""):
    parts = [title, ""]
    for ver, dt, cats in releases:
        head = "## [%s] - %s" % (ver, dt) if dt else "## [%s]" % ver
        parts += [head, ""]
        for cat, items in cats:
            parts.append("### %s" % cat)
            for it in items:
                parts.append("- %s" % it)
            parts.append("")
    if footer:
        parts += [footer, ""]
    return "\n".join(parts)


GOOD = cl(releases=[
    ("1.1.0", "2026-10-01", (("Added", ["new thing"]), ("Fixed", ["a bug"]))),
    ("1.0.0", "2026-09-01", (("Added", ["initial"]),)),
])


# ---------------------------------------------------------------- functional

def t_functional(tmp):
    f = chalint.lint(GOOD + "\n## [Unreleased]\n\n### Added\n- wip\n", AS_OF)
    record("functional", "well-formed changelog PASS", chalint.verdict(f) == "PASS", str(f))

    f = chalint.lint(GOOD.replace("# Changelog", "# History"), AS_OF)
    record("functional", "mis-titled H1 -> R001 (round-2 rule tightening)",
           len(codes(f, "R001")) == 1)

    f = chalint.lint(GOOD.replace("# Changelog", "# changelog"), AS_OF)
    record("functional", "case-insensitive title accepted", len(codes(f, "R001")) == 0)

    f = chalint.lint(cl(releases=[("1.0", "2026-09-01", (("Added", ["x"]),))]), AS_OF)
    record("functional", "two-part version -> R003", len(codes(f, "R003")) == 1)

    f = chalint.lint(cl(releases=[("1.0.0", "2026-02-30", (("Added", ["x"]),))]), AS_OF)
    record("functional", "Feb 30 -> R004 invalid date", len(codes(f, "R004")) == 1)

    f = chalint.lint(cl(releases=[("1.0.0", "2026-09-01", (("Added", ["x"]),)),
                                  ("1.1.0", "2026-10-01", (("Added", ["y"]),))]), AS_OF)
    record("functional", "ascending versions -> R005", len(codes(f, "R005")) == 1)

    f = chalint.lint(cl(releases=[("1.0.0", "2026-09-01", (("Added", ["x"]),)),
                                  ("1.0.0", "2026-10-01", (("Added", ["y"]),))]), AS_OF)
    record("functional", "duplicate version -> R006", len(codes(f, "R006")) == 1)

    f = chalint.lint(cl(releases=[("1.0.0", "2026-09-01", (("Notes", ["blah"]),))]), AS_OF)
    record("functional", "non-standard category -> R007 warn", chalint.verdict(f) == "WARN"
           and len(codes(f, "R007")) == 1)

    f = chalint.lint(cl(releases=[("1.0.0", "2026-09-01", (("Fixed", []),))]), AS_OF)
    record("functional", "category without bullets -> R008", len(codes(f, "R008")) == 1)

    f = chalint.lint(cl(releases=[("1.0.0", "2026-12-01", (("Added", ["x"]),))]), AS_OF)
    record("functional", "future date vs as-of -> R009", len(codes(f, "R009")) == 1)

    f = chalint.lint(GOOD + "\n## [Unreleased]\n\n### Added\n- wip\n", AS_OF)
    record("functional", "Unreleased without date is fine", chalint.verdict(f) == "PASS")

    f = chalint.lint(cl(releases=[("2.0.0-rc.1", "2026-10-01", (("Added", ["x"]),)),
                                  ("1.9.0", "2026-09-01", (("Added", ["y"]),))]), AS_OF)
    record("functional", "prerelease accepted, monotonic (only R010 warn)",
           len(codes(f, "R003")) == 0 and len(codes(f, "R005")) == 0
           and chalint.verdict(f) == "WARN")

    f = chalint.lint(GOOD, AS_OF)
    record("functional", "no Unreleased -> R010 warn only",
           len(codes(f, "R010")) == 1 and chalint.verdict(f) == "WARN")

    f = chalint.lint("# Changelog\n\n## [Unreleased]\n\n### Added\n- wip\n", AS_OF)
    record("functional", "Unreleased-only changelog PASS", chalint.verdict(f) == "PASS")

    f = chalint.lint(GOOD + "\n[1.1.0]: https://example.test/compare\n", AS_OF)
    record("functional", "trailing link refs ignored", len(codes(f, "R003")) == 0
           and chalint.verdict(f) == "WARN")

    f = chalint.lint(cl(releases=[("0.9.0", "2026-08-01", (("Changed", ["x"]), ("Removed", ["y"]), ("Security", ["z"]))),
                                  ("0.1.0", "2026-01-01", (("Deprecated", ["old"]),))]), AS_OF)
    record("functional", "all six categories recognized", chalint.verdict(f) == "WARN")


# ---------------------------------------------------------------- error paths

def t_error_paths(tmp):
    f = chalint.lint("", AS_OF)
    record("error", "empty file -> R001 FAIL", chalint.verdict(f) == "FAIL")

    f = chalint.lint("# Changelog\n", AS_OF)
    record("error", "title-only file -> no release findings", chalint.verdict(f) == "PASS")

    f = chalint.lint("random words\nno markdown at all\n", AS_OF)
    record("error", "headerless garbage -> R001", len(codes(f, "R001")) == 1)

    f = chalint.lint("# Changelog\n\n### Added\n- orphan h3\n", AS_OF)
    record("error", "H3 with no release section ignored", chalint.verdict(f) == "PASS")

    f = chalint.lint(cl(releases=[("1.0.0", "not-a-date", (("Added", ["x"]),))]), AS_OF)
    record("error", "garbage date -> R004", len(codes(f, "R004")) == 1)

    f = chalint.lint(cl(releases=[("1.0.0", "2026-13-01", (("Added", ["x"]),))]), AS_OF)
    record("error", "month 13 -> R004", len(codes(f, "R004")) == 1)

    f = chalint.lint(cl(releases=[("-1.0.0", "2026-09-01", (("Added", ["x"]),))]), AS_OF)
    record("error", "negative version -> R003", len(codes(f, "R003")) == 1)

    f = chalint.lint(cl(releases=[("v1.0.0", "2026-09-01", (("Added", ["x"]),))]), AS_OF)
    record("error", "v-prefix version -> R003", len(codes(f, "R003")) == 1)

    try:
        chalint.lint(GOOD, "not-a-date")
        ok = False
    except ValueError:
        ok = True
    record("error", "bad as-of raises ValueError (documented CLI contract)", ok)

    p = os.path.join(tmp, "crlf.md")
    with open(p, "w", encoding="utf-8", newline="") as fh:
        fh.write(GOOD.replace("\n", "\r\n"))
    r = chalint.lint_file(p, AS_OF)
    record("error", "CRLF file linted via lint_file", r["verdict"] in ("PASS", "WARN"))


# ---------------------------------------------------------------- extreme edges

def t_extreme_edges(tmp):
    many = [("1.%d.0" % (200 - i), "2026-%02d-%02d" % (1 + (i * 3) // 28, 1 + (i * 3) % 28),
             (("Added", ["item %d" % i]),)) for i in range(200)]
    f = chalint.lint(cl(releases=many), AS_OF)
    record("edge", "200 releases descending -> no R005", len(codes(f, "R005")) == 0)

    f = chalint.lint(cl(releases=[("1.0.0", "1900-01-01", (("Added", ["x"]),))]), AS_OF)
    record("edge", "year 1900 date valid", len(codes(f, "R004")) == 0)

    f = chalint.lint(cl(releases=[("1.0.0", "2026-02-29", (("Added", ["x"]),))]), AS_OF)
    record("edge", "2026-02-29 (not a leap year) -> R004", len(codes(f, "R004")) == 1)

    f = chalint.lint(cl(releases=[("1.0.0", "2024-02-29", (("Added", ["x"]),))]), AS_OF)
    record("edge", "2024-02-29 (leap year) valid", len(codes(f, "R004")) == 0)

    uni = cl(releases=[("1.0.0", "2026-09-01", (("Added", ["\u4fee\u590d\u4e86 \u2713 \u00fcnicode \U0001f680"]),))])
    f = chalint.lint(uni, AS_OF)
    record("edge", "unicode/emoji bullets parsed", chalint.verdict(f) == "WARN")

    big = cl(releases=[("1.0.0", "2026-09-01", (("Changed", ["x" * 100000]),))])
    f = chalint.lint(big, AS_OF)
    record("edge", "100KB single bullet tolerated", chalint.verdict(f) == "WARN")

    f = chalint.lint(cl(releases=[("1.0.0", "2026-09-01", (("Added", ["x"]),))], footer="[1.0.0]: https://x"), AS_OF)
    record("edge", "footer link ref not parsed as release", len(f) <= 2)

    f = chalint.lint(cl(releases=[("10.0.0", "2026-09-01", (("Added", ["x"]),)),
                                  ("9.99.99", "2026-08-01", (("Added", ["y"]),))]), AS_OF)
    record("edge", "two-digit major/minor ordering correct", len(codes(f, "R005")) == 0)

    f = chalint.lint(cl(title="# Changelog", releases=[("1.0.0", "2026-09-01", ())]), AS_OF)
    record("edge", "release with zero categories -> R007", len(codes(f, "R007")) == 1)

    f = chalint.lint(cl(releases=[("1.0.0", "2026-09-01", (("added", ["lowercase ok"]),))]), AS_OF)
    record("edge", "lowercase category accepted (case-insensitive)", len(codes(f, "R008")) == 0
           and chalint.verdict(f) == "WARN")

    p = os.path.join(tmp, "good.md")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(GOOD + "\n## [Unreleased]\n\n### Added\n- pending\n")
    r = chalint.lint_file(p, AS_OF)
    record("edge", "lint_file verdict PASS on full example", r["verdict"] == "PASS")

    import cli as cli_mod
    import io
    from contextlib import redirect_stdout
    bad = os.path.join(tmp, "bad.md")
    with open(bad, "w", encoding="utf-8") as fh:
        fh.write(cl(releases=[("1.0", "2026-13-40", ())]))
    def run_cli(*argv):
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                rc = cli_mod.main(list(argv))
        except SystemExit as e:
            rc = e.code if isinstance(e.code, int) else 2
        return rc, buf.getvalue()
    rc, _ = run_cli(p, "--as-of", AS_OF)
    record("edge", "cli good file -> 0", rc == 0)
    rc, _ = run_cli(bad)
    record("edge", "cli bad file -> 1", rc == 1)
    rc, out = run_cli(p, "--json")
    record("edge", "cli --json emits reports", rc == 0 and '"reports"' in out)
    rc, _ = run_cli("__missing__.md")
    record("edge", "cli missing file -> 2", rc == 2)


def main():
    tmp = tempfile.mkdtemp(prefix="chalint_test_")
    try:
        t_functional(tmp)
        t_error_paths(tmp)
        t_extreme_edges(tmp)
    finally:
        for f in os.listdir(tmp):
            try:
                os.unlink(os.path.join(tmp, f))
            except OSError:
                pass
        try:
            os.rmdir(tmp)
        except OSError:
            pass
    fails = [r for r in _results if r[2] == "FAIL"]
    for fam, name, status, detail in _results:
        print("[%s] %-10s %s%s" % (status, fam, name, (" | " + detail) if detail else ""))
    print("\n%d checks, %d failed" % (len(_results), len(fails)))
    print("SUMMARY: PASS %d/%d" % (len(_results) - len(fails), len(_results)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
