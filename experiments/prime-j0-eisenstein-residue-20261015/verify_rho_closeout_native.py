#!/usr/bin/env python3
"""Replay the closeout modes on every frozen Q and restart count."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / 'rho-closeout-fixtures'
COUNTS = (1, 8, 32, 128)
MODES = (
    ('openssl_globalwarm', '--pilot-rho-restart', 'openssl_globalwarm'),
    ('joint_triple81', '--pilot-rho-restart-joint-triple81'),
    ('joint_mixed76', '--pilot-rho-restart-joint-mixed76'),
)


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def parse(stdout: str) -> dict[str, str]:
    fields = {}
    for word in stdout.split():
        key, value = word.split('=', 1)
        assert key not in fields
        fields[key] = value
    return fields


def main(binary: Path, output: Path) -> None:
    manifest = json.loads((FIXTURES / 'manifest.json').read_text())
    assert len(manifest['fixtures']) == 32
    rows = []
    outputs = 0
    for entry in manifest['fixtures']:
        fixture = FIXTURES / entry['path']
        assert digest(fixture) == entry['sha256']
        expected = json.loads(fixture.read_text())['cases']
        for count in COUNTS:
            for mode, *flags in MODES:
                command = [str(binary), *flags, str(fixture), str(count)]
                result = subprocess.run(command, text=True, capture_output=True)
                assert result.returncode == 0, (command, result.stdout, result.stderr)
                assert not result.stderr.strip(), (command, result.stderr)
                fields = parse(result.stdout.strip())
                assert fields['verified'] == '1'
                assert fields['count'] == str(count)
                assert fields['mode'] == mode
                assert fields['point'] == expected[count - 1]['point_hex']
                online = float(fields['online_ms'])
                prep = float(fields['target_preparation_ms'])
                evaluation = float(fields['restart_eval_ms'])
                assert online >= 0 and prep >= 0 and evaluation >= 0
                assert abs(online - prep - evaluation) <= 0.000002
                if mode == 'openssl_globalwarm':
                    assert float(fields['openssl_warmup_ms']) > 0
                rows.append({'fixture': entry['path'], 'fixture_sha256': entry['sha256'],
                             'count': count, 'mode': mode,
                             'stdout': result.stdout.strip()})
                outputs += count
    receipt = {'schema': 'rho-closeout-native-replay-v1',
               'status': 'exact_output_replay_passed',
               'timing_status': 'local_diagnostic_only',
               'binary_sha256': digest(binary),
               'fixture_manifest_sha256': digest(FIXTURES / 'manifest.json'),
               'commands': len(rows), 'exact_outputs': outputs, 'rows': rows}
    output.write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': receipt['status'], 'commands': len(rows),
                      'exact_outputs': outputs, 'binary_sha256': receipt['binary_sha256']},
                     sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    main(args.binary, args.output)
