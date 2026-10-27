"""Exercise digest, canonical-encoding and rational-normalization rejection."""
import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

import cache_codec

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / 'inputs.json').read_text())
POST = json.loads((HERE / 'post_inputs.json').read_text())
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == POST['controls_sha256']


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


def main():
    H = module(ROOT / PLAN['source_path'], 'hecke13_cache_negative_controls')
    artifact = ROOT / json.loads((HERE / 'build-result.json').read_text())['artifact_path']
    raw = artifact.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == POST['artifact_sha256']
    results = []
    with tempfile.TemporaryDirectory(dir=HERE) as folder:
        temp = Path(folder)

        def expect(name, data, expected, actual_filename_digest=None):
            digest = actual_filename_digest or POST['artifact_sha256']
            path = temp / f'hecke13-{digest}.json'
            path.write_bytes(data)
            try:
                cache_codec.load_artifact(path, digest, H, PLAN['source_sha256'])
            except (ValueError, AssertionError) as error:
                assert expected in str(error) if expected else type(error) is AssertionError
                results.append({'control': name, 'status': 'REJECTED_AS_EXPECTED',
                                'exception': type(error).__name__,
                                'reason': str(error) if expected else 'noncanonical rational'})
            else:
                raise AssertionError(f'NEGATIVE_CONTROL_ACCEPTED:{name}')

        expect('changed_byte', raw[:-1] + b' ', 'ARTIFACT_DIGEST_MISMATCH')
        pretty = (json.dumps(json.loads(raw), indent=2, sort_keys=True) + '\n').encode()
        expect('noncanonical_json', pretty, 'ARTIFACT_NONCANONICAL_JSON',
               hashlib.sha256(pretty).hexdigest())
        obj = json.loads(raw)
        first = next(item['terms'][0][2] for item in obj['funcs'] if item['terms'])
        first[0] *= 2
        first[1] *= 2
        bad_rational = cache_codec.canonical_bytes(obj)
        expect('nonreduced_rational', bad_rational, None,
               hashlib.sha256(bad_rational).hexdigest())
    out = {'schema': 'hecke-d79-function-cache-controls-v1', 'status': 'PASS',
           'artifact_sha256': POST['artifact_sha256'], 'results': results}
    (HERE / 'negative-controls.json').write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': 'PASS', 'controls': len(results)}))


if __name__ == '__main__':
    main()
