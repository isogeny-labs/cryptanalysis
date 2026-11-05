#!/usr/bin/env python3
"""Instruction-cost ledger checker.

A cost model publishes a number.  That number is almost always a sum of stage
costs, compared to a previous version, converted into bits, and rounded for the
headline.  Each of those four steps is easy to get wrong by hand, and each is
exactly checkable.

A ledger is a JSON document (see ``examples/``) with:

    name, unit         what the number counts, per what
    rows               one entry per stage: stage, count, optional "per"
    normalization      optional {factor, note}: total = sum(rows) * factor
    declared_total     the number as published
    baseline           optional: same shape, for the version being improved on
    improvement        optional {bits}: log2(baseline_total / declared_total)
    break_even         optional: which extra work is paid for which saving
    claim              optional: the rounded headline and its exact value

``check`` verifies:

  1. rows sum to the declared total, exactly, after normalization;
  2. the baseline rows sum to the baseline total;
  3. the two sides itemize the same stages, and the per-stage deltas add up to
     the difference of the totals;
  4. the quoted improvement in bits really is log2(before/after);
  5. every break-even inequality holds with the stated fan-outs;
  6. a published claim is the least ``decimals``-place value at or above the
     exact quantity.

It does not verify that the counts are true, that the bound is sound, or that
the error set is complete.  Those are proof obligations; see
docs/INSTRUCTION-COST-ACCOUNTING.md and docs/REVIEW-CHECKLIST-COST-CLAIMS.md.

Usage:
    python3 tools/cost/ledger.py check tools/cost/examples/*.json
    python3 tools/cost/ledger.py template > my-ledger.json
"""

import argparse
import json
import math
import sys
from fractions import Fraction

MAX_DECIMALS = 30


class LedgerError(Exception):
    """A structural problem with the ledger document itself."""


def _number(value, field):
    """Parse a JSON number as an exact Fraction.

    Strings are accepted and preferred for anything whose digits matter:
    ``1206.5`` as a float is exact, but a 17-digit float is not.
    """
    if isinstance(value, bool) or value is None:
        raise LedgerError("%s: expected a number, got %r" % (field, value))
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise LedgerError("%s: not finite: %r" % (field, value))
        return Fraction(str(value))
    if isinstance(value, str):
        try:
            return Fraction(value.strip())
        except (ValueError, ZeroDivisionError):
            raise LedgerError("%s: not a decimal number: %r" % (field, value))
    raise LedgerError("%s: expected a number, got %r" % (field, value))


def _rows(doc, where):
    rows = doc.get("rows")
    if not isinstance(rows, list) or not rows:
        raise LedgerError("%s.rows: expected a non-empty list" % where)
    out = []
    seen = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise LedgerError("%s.rows[%d]: expected an object" % (where, index))
        stage = row.get("stage")
        if not isinstance(stage, str) or not stage.strip():
            raise LedgerError("%s.rows[%d].stage: expected a name" % (where, index))
        if stage in seen:
            raise LedgerError("%s.rows: duplicate stage %r" % (where, stage))
        seen.add(stage)
        count = _number(row.get("count"), "%s.rows[%s].count" % (where, stage))
        if count < 0:
            raise LedgerError("%s.rows[%s].count: negative" % (where, stage))
        out.append({"stage": stage, "count": count, "per": row.get("per")})
    return out


def _factor(doc, where):
    normalization = doc.get("normalization")
    if normalization is None:
        return Fraction(1), "none"
    if not isinstance(normalization, dict):
        raise LedgerError("%s.normalization: expected an object" % where)
    factor = _number(normalization.get("factor"), "%s.normalization.factor" % where)
    if factor <= 0:
        raise LedgerError("%s.normalization.factor: must be positive" % where)
    note = normalization.get("note") or ""
    return factor, note


def _decimal_string(value, places):
    """Render an exact Fraction with exactly ``places`` decimals (truncating)."""
    scaled = value * (10 ** places)
    sign = "-" if scaled < 0 else ""
    whole = abs(scaled.numerator) // scaled.denominator
    digits = str(whole)
    if places:
        digits = digits.rjust(places + 1, "0")
        digits = digits[:-places] + "." + digits[-places:]
    return sign + digits


def _ceil_decimal(value, places):
    """Least multiple of 10**-places that is >= value."""
    scaled = value * (10 ** places)
    units = -((-scaled.numerator) // scaled.denominator)
    return Fraction(units, 10 ** places)


def check_ledger(doc):
    """Return a list of {name, ok, detail} checks plus a summary dict."""
    if not isinstance(doc, dict):
        raise LedgerError("ledger: expected a JSON object")
    unit = doc.get("unit")
    if not isinstance(unit, str) or not unit.strip():
        raise LedgerError("ledger.unit: expected a description such as "
                          "'instructions per step'")

    rows = _rows(doc, "ledger")
    factor, factor_note = _factor(doc, "ledger")
    total = _number(doc.get("declared_total"), "ledger.declared_total")
    row_sum = sum((row["count"] for row in rows), Fraction(0))
    expected = row_sum * factor

    checks = []

    def record(name, ok, detail):
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    record("unit", True, unit)
    record("rows sum to declared total", expected == total,
           "%s rows -> %s (factor %s%s); declared %s"
           % (len(rows), _decimal_string(expected, 6), factor,
              "" if factor_note is None else ", " + str(factor_note),
              _decimal_string(total, 6)))

    summary = {
        "unit": unit,
        "row_sum": str(expected),
        "declared_total": str(total),
    }

    baseline = doc.get("baseline")
    deltas = None
    if baseline is not None:
        if not isinstance(baseline, dict):
            raise LedgerError("ledger.baseline: expected an object")
        base_rows = _rows(baseline, "baseline")
        base_factor, _ = _factor(baseline, "baseline")
        base_total = _number(baseline.get("declared_total"),
                             "baseline.declared_total")
        base_expected = sum((row["count"] for row in base_rows), Fraction(0)) * base_factor
        record("baseline rows sum to baseline total", base_expected == base_total,
               "%s rows -> %s; declared %s"
               % (len(base_rows), _decimal_string(base_expected, 6),
                  _decimal_string(base_total, 6)))

        after = {row["stage"]: row["count"] * factor for row in rows}
        before = {row["stage"]: row["count"] * base_factor for row in base_rows}
        missing = sorted(set(after) ^ set(before))
        record("baseline itemizes the same stages", not missing,
               "stages only on one side: %s" % (", ".join(missing) if missing else "none"))

        deltas = {stage: after[stage] - before[stage] for stage in after if stage in before}
        delta_sum = sum(deltas.values(), Fraction(0))
        record("stage deltas add up to the total delta",
               delta_sum == (total - base_total),
               "sum of deltas %s vs total delta %s"
               % (_decimal_string(delta_sum, 6),
                  _decimal_string(total - base_total, 6)))

        summary["baseline_total"] = str(base_total)
        summary["deltas"] = {stage: str(delta) for stage, delta in deltas.items()}

        improvement = doc.get("improvement")
        if improvement is not None:
            if not isinstance(improvement, dict):
                raise LedgerError("ledger.improvement: expected an object")
            if total <= 0 or base_total <= 0:
                record("improvement is log2(before/after)", False,
                       "totals must be positive")
            else:
                declared = _number(improvement.get("bits"), "improvement.bits")
                computed = math.log2(float(base_total / total))
                stated = improvement.get("bits")
                tolerance = improvement.get("tolerance")
                if tolerance is not None:
                    tol = float(_number(tolerance, "improvement.tolerance"))
                elif isinstance(stated, str) and "." in stated:
                    tol = 0.5 * 10 ** (-len(stated.split(".")[1]))
                else:
                    tol = 1e-9
                ok = abs(computed - float(declared)) <= tol
                record("improvement is log2(before/after)", ok,
                       "computed %.12f bits vs declared %s (tolerance %g)"
                       % (computed, _decimal_string(declared, 6), tol))
                summary["bits"] = computed

        for item in doc.get("break_even") or []:
            if not isinstance(item, dict):
                raise LedgerError("ledger.break_even: expected objects")
            moved = item.get("moved")
            saved = item.get("saved")
            if moved not in deltas or saved not in deltas:
                record("break-even %s -> %s" % (moved, saved), False,
                       "stage missing on one side; itemize it in both ledgers")
                continue
            moved_fanout = _number(item.get("moved_fanout", 1), "break_even.moved_fanout")
            saved_fanout = _number(item.get("saved_fanout", 1), "break_even.saved_fanout")
            paid = deltas[moved] * moved_fanout
            gained = -deltas[saved] * saved_fanout
            record("break-even %s -> %s" % (moved, saved), paid < gained,
                   "extra %s x %s = %s < saved %s x %s = %s"
                   % (moved, moved_fanout, _decimal_string(paid, 6),
                      saved, saved_fanout, _decimal_string(gained, 6)))

    claim = doc.get("claim")
    if claim is not None:
        if not isinstance(claim, dict):
            raise LedgerError("ledger.claim: expected an object")
        exact = _number(claim.get("exact"), "claim.exact")
        places = claim.get("decimals")
        if not isinstance(places, int) or isinstance(places, bool) or not 0 <= places <= MAX_DECIMALS:
            raise LedgerError("claim.decimals: expected an integer in 0..%d" % MAX_DECIMALS)
        declared_text = claim.get("declared")
        if not isinstance(declared_text, str):
            raise LedgerError("claim.declared: expected a string so trailing "
                              "zeros survive")
        expected_text = _decimal_string(_ceil_decimal(exact, places), places)
        ok = declared_text.strip() == expected_text
        record("claim is the least %d-place value at or above exact" % places, ok,
               "exact %s -> %s; declared %s"
               % (_decimal_string(exact, places + 3), expected_text, declared_text))
        summary["claim"] = expected_text

    summary["ok"] = all(check["ok"] for check in checks)
    return checks, summary


def _print_report(path, checks, summary):
    print("%s" % path)
    width = max(len(check["name"]) for check in checks)
    for check in checks:
        print("  [%s] %-*s  %s" % ("ok" if check["ok"] else "FAIL", width,
                                   check["name"], check["detail"]))
    print("  -> %s" % ("PASS" if summary["ok"] else "FAIL"))
    return summary["ok"]


TEMPLATE = {
    "name": "what this ledger costs",
    "unit": "instructions per unit",
    "normalization": {"factor": 1, "note": "rows are already per unit"},
    "rows": [
        {"stage": "stage-a", "per": "unit", "count": 100},
        {"stage": "stage-b", "per": "unit", "count": 50},
    ],
    "declared_total": 150,
    "baseline": {
        "rows": [
            {"stage": "stage-a", "per": "unit", "count": 100},
            {"stage": "stage-b", "per": "unit", "count": 80},
        ],
        "declared_total": 180,
    },
    "improvement": {"bits": "0.263034"},
    "break_even": [
        {"moved": "stage-a", "saved": "stage-b", "moved_fanout": 1, "saved_fanout": 1}
    ],
    "claim": {"quantity": "log2(T)", "exact": "124.9214702494968",
              "decimals": 12, "declared": "124.921470249497"},
}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="check one or more ledger files")
    check.add_argument("files", nargs="+")
    check.add_argument("--json", action="store_true", help="machine-readable output")

    sub.add_parser("template", help="print a starter ledger")

    args = parser.parse_args(argv)

    if args.command == "template":
        print(json.dumps(TEMPLATE, indent=2))
        return 0

    results = []
    ok = True
    for path in args.files:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                doc = json.load(handle)
            checks, summary = check_ledger(doc)
        except (OSError, ValueError, LedgerError) as error:
            checks, summary = [{"name": "parse", "ok": False, "detail": str(error)}], {"ok": False}
            ok = False
        else:
            ok = ok and summary["ok"]
        results.append({"path": path, "checks": checks, "summary": summary})
        if not args.json:
            _print_report(path, checks, summary)

    if args.json:
        print(json.dumps({"ok": ok, "results": results}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
