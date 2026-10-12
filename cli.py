"""CLI for changelog-semantic-lint."""
import argparse
import json
import sys

import chalint


def main(argv=None):
    ap = argparse.ArgumentParser(prog="changelog-semantic-lint",
                                 description="Lint CHANGELOG.md: Keep-a-Changelog structure, semver monotonicity, calendar-date validity.")
    ap.add_argument("paths", nargs="+", help="CHANGELOG files")
    ap.add_argument("--as-of", default=None, help="reference date YYYY-MM-DD for future-date warnings (default: none)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    reports = []
    for p in args.paths:
        try:
            reports.append(chalint.lint_file(p, args.as_of))
        except OSError as e:
            print("error: %s" % e, file=sys.stderr)
            return 2

    if args.json:
        print(json.dumps({"reports": reports}, indent=2, ensure_ascii=False))
    else:
        for r in reports:
            print("%-6s %s (%d finding(s))" % (r["verdict"], r["path"], len(r["findings"])))
            for f in r["findings"]:
                print("  L%-4d %s %s: %s" % (f["line"], f["code"].upper(), f["severity"], f["message"]))
    return 1 if any(r["verdict"] == "FAIL" for r in reports) else 0


if __name__ == "__main__":
    sys.exit(main())
