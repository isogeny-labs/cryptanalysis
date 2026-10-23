"""Class-quotient/sign predictor, frozen before D1407/f6 producer work."""
from hashlib import sha256
from pathlib import Path
import json
from sage.all import BinaryQF, pari

P = Path(__file__).resolve().parent
ROOT = Path('/Volumes/SSD990-2')
LEGACY = ROOT / 'cryptanalysis-hecke-signed-component-model-20261022/RESULT.json'

def forecast(D):
    a1 = BinaryQF(2, 1, (1-D)//8).form_class()
    a3 = BinaryQF(2, 1, (1-9*D)//8).form_class()
    ram = BinaryQF(3, 3, (9-D)//12).form_class()
    h1, h3 = int(pari.qfbclassno(D)), int(pari.qfbclassno(9*D))
    o1, o3 = int(a1.order()), int(a3.order())
    assert h3 == 3*h1 and o3 % o1 == 0 and o3//o1 in (1, 3)
    exponent = next((k for k in range(o1) if k*a1 == ram), None)
    lift = 3//(o3//o1)
    touches = lift*(1 if exponent is not None else 2)
    cycles = 2*h3//o3
    assert 2*h3 % o3 == 0 and cycles % touches == 0
    pairs = h1
    components = cycles//touches
    mixed = exponent is not None and (o1//2)%2 == 0
    balanced = 0 if mixed else components
    return {'D': D, 'class_number_f1': h1, 'class_number_f3': h3,
            'norm2_order_f1': o1, 'norm2_order_f3': o3,
            'ramified_exponent_f1': exponent, 'lift_kernel_image_size': lift,
            'pair_cycle_touches': touches, 'cycle_count': cycles,
            'pair_count': pairs, 'component_count': components,
            'mixed_overlap': mixed, 'balanced_component_count': balanced,
            'floor_direction_rank': cycles+pairs-balanced}

def main():
    graphs = json.loads(LEGACY.read_text())['cases']
    sources = {'legacy': sha256(LEGACY.read_bytes()).hexdigest()}
    for label in ('D2703','D2991'):
        path = ROOT / f'cryptanalysis-hecke-{label}-f6-20261022/graph_{label}.json'
        graphs[label] = json.loads(path.read_text())
        sources[label] = sha256(path.read_bytes()).hexdigest()
    replay = {}
    for label, graph in sorted(graphs.items(), key=lambda item: int(item[0][1:])):
        expected = forecast(-int(label[1:]))
        observed = (graph['cycle_count'], graph['pair_count'], len(graph['components']),
                    graph['balanced_component_count'], graph['graph_floor_rank'])
        predicted = (expected['cycle_count'], expected['pair_count'], expected['component_count'],
                     expected['balanced_component_count'], expected['floor_direction_rank'])
        expected['observed'] = list(observed)
        expected['prediction_match'] = predicted == observed
        replay[label] = expected
    holdout = forecast(-1407)
    holdout.update({'class_columns_predicted': 384,
                    'rows_by_degree_predicted': {'2': 192, '3': 96},
                    'full_rank_predicted': 240,
                    'degree2_projection_rank_predicted': 180,
                    'degree3_projection_rank_predicted': 72,
                    'combined_projection_rank_predicted': 240-holdout['floor_direction_rank']})
    result = {'status': 'ELEVEN_CASE_MODEL_MATCH_FROZEN_D1407_FORECAST'
                       if all(x['prediction_match'] for x in replay.values())
                       else 'RETROSPECTIVE_MODEL_MISMATCH',
              'retrospective': replay, 'holdout_D1407': holdout,
              'source_hashes': sources,
              'script_sha256': sha256((P/'rank_predictor.py').read_bytes()).hexdigest(),
              'runtime_info_sha256': sha256((P/'sage_runtime.json').read_bytes()).hexdigest(),
              'conditional_assumptions': [
                  'two rational X0(11) sheets for each f3 ideal class',
                  'six floor children represent two parent classes with three lifts each',
                  'predicted incidence components are connected',
                  'uniform signed edges have no nonlocal path conflict'],
              'candidate_id': None, 'timing_claim': None}
    (P/'MODEL_BEFORE_HOLDOUT.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps({'status': result['status'], 'holdout': holdout}))

if __name__ == '__main__': main()
