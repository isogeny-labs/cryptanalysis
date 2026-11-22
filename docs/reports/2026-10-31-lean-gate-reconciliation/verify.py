#!/usr/bin/env python3
"""Replay the cryptanalysis 97-receipt / 77-addition Lean gate boundary."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
RUN = '5939def096fd181973e1abb7279644a8aa531557'
CURRENT = 'd3673ee089dd2a3a4ba15da087b95ebf2fb8e123'
INDEX = 'reports/lean-evidence-audit-20261021/evidence/corpus/cryptanalysis-corpus-index-20261021.json'
RECEIPT = 'reports/lean-current-corpus-20261025-main-update/receipt.json'
QUARTIC = 'tools/ci/quartic_certificates.json'
LOG = 'cryptanalysis-lean-gate-41077865188.log.gz'


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def git(repo: Path, *args: str) -> bytes:
    return subprocess.run(['git', '-C', str(repo), *args], check=True,
                          capture_output=True, timeout=120).stdout


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def tree(repo: Path, commit: str) -> tuple[dict[str, str], str]:
    require(git(repo, 'cat-file', '-t', commit).strip() == b'commit', 'missing source commit')
    oid = git(repo, 'rev-parse', commit + '^{tree}').decode().strip()
    out = {}
    for entry in git(repo, 'ls-tree', '-r', '-z', commit).split(b'\0'):
        if not entry:
            continue
        meta, name = entry.split(b'\t', 1)
        _, kind, blob = meta.decode().split()
        if kind == 'blob':
            path = name.decode()
            require(path not in out, 'duplicate path')
            out[path] = blob
    return out, oid


def read_json(repo: Path, commit: str, path: str) -> dict:
    return json.loads(git(repo, 'show', commit + ':' + path))


def relevant(path: str) -> bool:
    basename = path.rsplit('/', 1)[-1]
    return (path.startswith('tools/lean/') or
            path == '.github/workflows/lean-proof-gate.yml' or
            path == QUARTIC or path == RECEIPT or
            path.startswith('reports/lean-evidence-audit-20261021/evidence/corpus/') or
            path.startswith('reports/ghs-pr-1104-main-integration-20261025/') or
            basename in {'lean-toolchain', 'lakefile.toml', 'lakefile.lean',
                         'lake-manifest.json', 'DEPENDENCIES.json'})


def build(repo: Path) -> dict:
    old, old_tree = tree(repo, RUN)
    new, new_tree = tree(repo, CURRENT)
    old_lean = {p: b for p, b in old.items() if p.endswith('.lean')}
    new_lean = {p: b for p, b in new.items() if p.endswith('.lean')}
    require(old_lean == new_lean and len(new_lean) == 184,
            'Lean path or source blob changed after hosted gate')
    protected = sorted(p for p in set(old) | set(new) if relevant(p))
    require(all(old.get(p) == new.get(p) for p in protected),
            'gate, dependency, or frozen evidence input changed after hosted run')
    index = read_json(repo, CURRENT, INDEX)
    receipt = read_json(repo, CURRENT, RECEIPT)
    quartic = read_json(repo, CURRENT, QUARTIC)
    archived = {row['source'] for row in index['files']}
    fresh = set(receipt['fresh_native_files'])
    require(len(archived) == 93 and len(fresh) == 7 and
            len(archived | fresh) == receipt['current_lean_files'] == 97,
            '97-source receipt partition changed')
    outside = set(new_lean) - archived - fresh
    require(len(outside) == 87, 'outside-receipt path count changed')
    reviewed = {row['path'] for row in quartic['formal']}
    groups = {
        'tools_lean_outside_corpus': {p for p in outside if p.startswith('tools/lean/')},
        'reviewed_quartic': outside & reviewed,
        'known_label': outside & {'docs/known-label-next-leads-20261028/Algebra.lean'},
        'pair_index': outside & {'docs/known-label-pair-index-20261029/PairIndex.lean'},
        'hasse': outside & {'bindings/rust/curve-audit/formal/HasseSquareBounds.lean'},
        'core_compatibility': outside & {'reports/ci-xedni-proof-elaboration-repair-20261030/xedni-core-arithmetic-compatibility-controls-20261030.lean'},
    }
    used = set().union(*groups.values())
    groups['generic_hecke_or_xedni'] = outside - used
    require([len(groups[k]) for k in groups] == [10, 37, 1, 1, 1, 1, 36],
            'addition dispatch partition changed')
    require(all((p.startswith('experiments/hecke-') or
                 p.startswith('experiments/xedni-')) and '/formal/' in p
                for p in groups['generic_hecke_or_xedni']),
            'generic source is outside admitted native gate route')
    require(len(set().union(*groups.values())) == 87 and
            sum(map(len, groups.values())) == 87,
            'dispatch groups overlap or omit paths')
    run = json.loads((HERE / 'run.json').read_bytes())
    require(run['headSha'] == RUN and run['status'] == 'completed' and
            run['conclusion'] == 'success' and
            len(run['jobs']) == 1 and run['jobs'][0]['name'] == 'corpus' and
            run['jobs'][0]['conclusion'] == 'success', 'hosted run status differs')
    archive = (HERE / LOG).read_bytes()
    log = gzip.decompress(archive)
    require(log.count(b'native added theorem modules checked: 77') == 1,
            'hosted log lacks 77-module terminal marker')
    require(b'python3 tools/lean/current-corpus-gate.py --check-receipt' in log,
            'hosted log lacks exact gate command')
    return {
        'schema': 'cryptanalysis-lean-gate-reconciliation/v1',
        'run_commit': RUN, 'run_tree': old_tree,
        'current_commit': CURRENT, 'current_tree': new_tree,
        'github_run': 41077865188,
        'run_json_sha256': sha((HERE / 'run.json').read_bytes()),
        'hosted_log_gzip_sha256': sha(archive),
        'hosted_log_uncompressed_sha256': sha(log),
        'protected_input_paths_unchanged': len(protected),
        'lean_paths_and_blobs_unchanged': len(new_lean),
        'tracked_lean_files': 184,
        'native_corpus_sources': 174,
        'historical_receipt_sources': 97,
        'outside_historical_receipt': 87,
        'native_admitted_additions': 77,
        'tool_tree_sources_outside_corpus': 10,
        'groups': {k: sorted(v) for k, v in groups.items()},
        'claim_boundary': 'Native gate success is source/build/axiom evidence at these pins; it does not provide theorem-meaning review or historical execution validation.',
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', type=Path, required=True)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    result = build(args.repo)
    data = (json.dumps(result, sort_keys=True, indent=2) + '\n').encode()
    dest = HERE / 'result.json'
    if args.write:
        with dest.open('xb') as file:
            file.write(data)
    else:
        require(dest.read_bytes() == data, 'result differs from exact replay')
    print('PASS 184 Lean files; 97 historical receipt; 77 additional native checks; 10 tool-tree sources')


if __name__ == '__main__':
    main()
