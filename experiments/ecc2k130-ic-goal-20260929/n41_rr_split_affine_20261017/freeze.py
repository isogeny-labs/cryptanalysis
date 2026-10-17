"""Freeze a source-only selected box panel before split-minor evaluation."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / 'n41_rr_joint_box_rank_20261017'
SOURCE = ROOT / 'n41_sixpair_shared_target_20261017/join_input.tsv'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    panel = json.loads((PRIOR / 'panel.json').read_text())
    assert len(panel['panels']) == 97
    assert panel['source_sha256'] == sha(SOURCE)
    indices = [*range(32), *range(32, 36), *range(64, 97)]
    assert len(indices) == 69
    record = {'status': 'FROZEN_N41_SPLIT_MINOR_AFFINE_SCREEN',
              'candidate_id': None, 'curve_id': 'EC1N41Ckb1h7d5e80d3c4d0',
              'panel_indices': indices, 'one_worker': True,
              'wall_cap_seconds': 180, 'rss_observational_boundary_bytes': 4*1024**3,
              'input_law': 'frozen source-valid sign, root-sign, two-code and positive witness boxes',
              'source_sha256': {'runner': sha(HERE / 'run.py'),
                                'panel': sha(PRIOR / 'panel.json'),
                                'source': sha(SOURCE),
                                'prior_result': sha(PRIOR / 'result.json')}}
    with (HERE / 'protocol.json').open('x') as file:
        json.dump(record, file, indent=2, sort_keys=True)
        file.write('\n')
    print(record['status'], len(indices))


if __name__ == '__main__':
    main()
