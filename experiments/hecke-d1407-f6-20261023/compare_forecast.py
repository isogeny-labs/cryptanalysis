"""Compare the frozen class-quotient rank forecast to repaired exact evidence."""
from hashlib import sha256
from pathlib import Path
import json

P=Path(__file__).resolve().parent
sha=lambda q:sha256(q.read_bytes()).hexdigest()

def main():
    model_path=P/'MODEL_BEFORE_HOLDOUT.json'
    protocol_path=P/'protocol_D1407.json'
    data_path=P/'regularized/data/exp11_class_walk_D1407_f6.json'
    audit_path=P/'regularized/audit_D1407.json'
    floor_path=P/'regularized/floor_D1407.json'
    graph_path=P/'regularized/graph_D1407.json'
    model=json.loads(model_path.read_text())['holdout_D1407']
    protocol=json.loads(protocol_path.read_text())
    data=json.loads(data_path.read_text())
    floor=json.loads(floor_path.read_text())
    graph=json.loads(graph_path.read_text())
    observed={'class_columns':data['class_size'],
              'rows_by_degree':data['relations_per_l'],
              'full_rank':data['rank'],
              'degree2_projection_rank':floor['ranks']['QQ']['2'][1],
              'degree3_projection_rank':floor['ranks']['QQ']['3'][1],
              'combined_projection_rank':floor['ranks']['QQ']['2+3'][1],
              'cycle_count':graph['cycle_count'],
              'pair_count':graph['pair_count'],
              'pair_cycle_touches':sorted(set(graph['pair_cycle_touch_count'].values())),
              'component_count':len(graph['components']),
              'mixed_overlap':any(not edge['locally_uniform'] for edge in graph['edges']),
              'balanced_component_count':graph['balanced_component_count'],
              'floor_direction_rank':graph['graph_floor_rank']}
    expected={'class_columns':model['class_columns_predicted'],
              'rows_by_degree':model['rows_by_degree_predicted'],
              'full_rank':model['full_rank_predicted'],
              'degree2_projection_rank':model['degree2_projection_rank_predicted'],
              'degree3_projection_rank':model['degree3_projection_rank_predicted'],
              'combined_projection_rank':model['combined_projection_rank_predicted'],
              'cycle_count':model['cycle_count'],
              'pair_count':model['pair_count'],
              'pair_cycle_touches':[model['pair_cycle_touches']],
              'component_count':model['component_count'],
              'mixed_overlap':model['mixed_overlap'],
              'balanced_component_count':model['balanced_component_count'],
              'floor_direction_rank':model['floor_direction_rank']}
    mismatches={k:{'expected':expected[k],'observed':observed[k]}
                for k in expected if expected[k]!=observed[k]}
    assert not mismatches and graph['all_match']
    assert json.loads(audit_path.read_text())['status']=='VERIFIED_D1407_F6_MATRIX'
    assert protocol['model_sha256']==sha(model_path)
    result={'status':'PROSPECTIVE_D1407_RANK_FORECAST_MATCH_AFTER_J_REPAIR',
            'frozen_model_sha256':sha(model_path),'frozen_protocol_sha256':sha(protocol_path),
            'repaired_data_sha256':sha(data_path),'audit_sha256':sha(audit_path),
            'floor_sha256':sha(floor_path),'graph_sha256':sha(graph_path),
            'script_sha256':sha(P/'compare_forecast.py'),
            'expected':expected,'observed':observed,'mismatches':mismatches,
            'candidate_id':None,'timing_claim':None}
    (P/'forecast_comparison.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'checks':len(expected),'mismatches':0}))

if __name__=='__main__':main()
