#!/usr/bin/env python3
"""Bind the GLV no-worse Lean counterexample to frozen code and JSON values."""
import argparse
import hashlib
import json
import re
from decimal import Decimal
from pathlib import Path

STUDY = Path(__file__).resolve().parents[2]
ANALYZE_SHA = 'd176871072c0ccd109357aa8369b63e0811573a36bb8dc64f69627f3997b4a22'
RESULTS_SHA = 'f196d804397b7a44b3392c11c5b6c99e4154ae70c11fb687f6e376b999911550'
SCALE = Decimal(10) ** 16


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scaled(value):
    exact = value * SCALE
    require(exact == int(exact), 'published decimal exceeds 16 places')
    return int(exact)


def check(study):
    code = study / 'analyze.py'
    results = study / 'results.json'
    proof = study / 'formal/no-worse-20261108/NoWorseLogic.lean'
    blind = study / 'formal/no-worse-20261108/BLIND_INPUT.json'
    require(digest(code) == ANALYZE_SHA, 'frozen analysis source changed')
    require(digest(results) == RESULTS_SHA, 'frozen result JSON changed')
    source = code.read_text()
    require('if ci[0] > 1:' in source, 'pooled-size reject predicate changed')
    require('"pass": not worse' in source, 'pooled-size pass predicate changed')
    data = json.loads(results.read_text(), parse_float=Decimal)
    require(data['no_worse']['pass'] is True, 'historical no-worse pass changed')
    require(data['no_worse']['sizes_wholly_worse'] == [], 'historical rejection set changed')
    expected_sizes = [tuple(scaled(x) for x in data['by_size'][str(b)]['ci_bonferroni'])
                      for b in (40, 41, 42, 43)]
    expected_j0 = tuple(scaled(x) for x in data['by_family']['j0']['ci95'])
    expected_point = scaled(data['by_family']['j0']['geomean_over_main'])
    card = json.loads(blind.read_text())
    require(card['schema'] == 'glv-cap-no-worse-blind-input/v1', 'blind input schema changed')
    require(card['scale'] == int(SCALE), 'blind input scale changed')
    require(card['rule'] == 'pooled-size check passes exactly when every supplied pooled-size lower endpoint is at most scale',
            'blind input rule changed')
    require([tuple(card['pooled_size_intervals'][str(b)]) for b in (40, 41, 42, 43)] == expected_sizes,
            'blind input pooled intervals differ from JSON')
    require(tuple(card['separate_family_interval']) == expected_j0,
            'blind input family interval differs from JSON')
    require(card['separate_family_point_estimate'] == expected_point,
            'blind input family point differs from JSON')
    text = proof.read_text()

    def one(pattern):
        match = re.search(pattern, text, re.S)
        require(match is not None, 'Lean definition missing or changed: ' + pattern)
        return match

    require(int(one(r'def one : Nat := (\d+)').group(1)) == int(SCALE), 'Lean scale changed')
    require('pooledSizes.all (fun i => decide (i.lower ≤ one)) = true' in text,
            'Lean decision predicate changed')
    sizes = one(r'def pooled40to43 : List Interval :=\s*\[(.*?)\]').group(1)
    observed_sizes = [tuple(map(int, p)) for p in re.findall(r'⟨(\d+),\s*(\d+)⟩', sizes)]
    require(observed_sizes == expected_sizes, 'Lean pooled-size endpoints differ from JSON')
    observed_j0 = tuple(map(int, one(r'def j0Family : Interval :=\s*⟨(\d+),\s*(\d+)⟩').groups()))
    require(observed_j0 == expected_j0, 'Lean j0 endpoints differ from JSON')
    observed_point = int(one(r'def j0PointEstimate : Nat := (\d+)').group(1))
    require(observed_point == expected_point, 'Lean j0 point estimate differs from JSON')
    require(len(observed_sizes) == 4, 'wrong pooled-size count')
    return {'source_sha256': digest(code), 'results_sha256': digest(results),
            'pooled_size_intervals_scaled': observed_sizes,
            'j0_interval_scaled': observed_j0, 'j0_point_scaled': observed_point}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--study-dir', type=Path, default=STUDY)
    args = ap.parse_args()
    print(json.dumps(check(args.study_dir), sort_keys=True))
