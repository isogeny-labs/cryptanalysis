"""Independent p1367 pair, gradient, inverse-certificate, and source-image audit."""
import importlib.util
import json
from collections import Counter, defaultdict
from hashlib import sha256
from math import gcd
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
P=1367


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def key(row):
    return tuple(row['source_ainvs']),tuple(row['pair'])


def main():
    dependencies=json.loads((HERE/'audit_dependencies.json').read_text())
    for record in dependencies.values():
        assert sha256(Path(record['path']).read_bytes()).hexdigest()==record['sha256']
    prior=load('p1231_audit_math',ROOT/'experiments/hecke-432-prime1039-collision-prediction-20261026/audit_holdout.py')
    prior.P=P
    dual=load('dual_math',ROOT/'experiments/hecke-432-collision-singular-locus-20261026/audit.py')
    protocol_path=HERE/'protocol.json'
    protocol=json.loads(protocol_path.read_text())
    inverse_protocol_path=HERE/'inverse_protocol.json'
    inverse_protocol=json.loads(inverse_protocol_path.read_text())
    source_protocol_path=HERE/'source_protocol.json'
    source_protocol=json.loads(source_protocol_path.read_text())
    for record in list(protocol['inputs'].values())+list(inverse_protocol['inputs'].values())+list(source_protocol['inputs'].values()):
        assert sha256(Path(record['path']).read_bytes()).hexdigest()==record['sha256']
    screen=json.loads((HERE/'screen_result.json').read_text())
    inverse=json.loads((HERE/'holdout_result.json').read_text())
    rows_path=HERE/'source_free_rows.json'
    rows=json.loads(rows_path.read_text())
    assert screen['protocol_sha256']==sha256(protocol_path.read_bytes()).hexdigest()
    assert screen['screen_source_sha256']==sha256((HERE/'screen.py').read_bytes()).hexdigest()
    assert screen['rows_sha256']==sha256(rows_path.read_bytes()).hexdigest()
    assert inverse['protocol_sha256']==sha256(inverse_protocol_path.read_bytes()).hexdigest()
    assert inverse['screen_result_sha256']==sha256((HERE/'screen_result.json').read_bytes()).hexdigest()
    assert inverse['source_code_sha256']==sha256((HERE/'recover_sage.py').read_bytes()).hexdigest()
    assert inverse['status']=='PASS_P1367_J1728_27_PATH_PREDICTION'
    assert len(rows)==screen['resolvent_pairs']==1380
    valid_rows=[r for r in rows if r['status']=='VALID']
    assert len(valid_rows)==screen['valid_triples']==1376
    pair_by_key={(*r['C_point'],*r['E_point']):r for r in rows}
    assert len(pair_by_key)==len(rows)
    resolvent=json.loads(Path(protocol['inputs']['resolvent']['path']).read_text())
    bterms=json.loads(Path(protocol['inputs']['b_resolvent']['path']).read_text())['terms']
    coeffs_by_c={}
    for c in prior.curve_points('C'):
        coeffs=[0]*13
        for term in resolvent['terms']:
            i=term['x_E_exponent']
            coeffs[i]=(coeffs[i]+int(term['integer_coefficient'])*pow(c[0],term['x_C_exponent'],P)*pow(c[1],term['y_C_exponent'],P))%P
        coeffs_by_c[c]=coeffs
    expected_pairs={(*c,*e) for c,coeffs in coeffs_by_c.items() for e in prior.curve_points('E') if prior.horner(coeffs,e[0])==0}
    assert set(pair_by_key)==expected_pairs
    predicted={}
    for row in valid_rows:
        c,e,b=row['C_point'],row['E_point'],row['B_point']
        value_t,dt=dual.dual_value(bterms,c,b[0],P,'T')
        value_c,dc=dual.dual_value(bterms,c,b[0],P,'C')
        db=2*b[1]*dt%P
        assert value_t==value_c==0
        assert (dt,dc,db)==(row['dT'],row['dC'],row['restricted_B_derivative'])
        flag=dc==db==0
        assert flag==row['predicted_double']
        predicted[(*c,*e,*b)]=flag
    assert sum(predicted.values())==screen['predicted_doubles']==8
    gcd_path=HERE/'holdout_gcd_rows.json'
    gcd_rows=json.loads(gcd_path.read_text())
    assert inverse['gcd_rows_sha256']==sha256(gcd_path.read_bytes()).hexdigest()
    assert len(gcd_rows)==len(valid_rows)
    squares=defaultdict(list)
    for y in range(P): squares[y*y%P].append(y)
    checked=set()
    for row in gcd_rows:
        c,e=row['C_point'],row['E_point']
        pairkey=(*c,*e)
        assert pairkey in pair_by_key and pairkey not in checked
        checked.add(pairkey)
        polynomial=prior.specialize(bterms,c)
        cubic=[(-64)%P,0,(-e[0])%P,1]
        common,s,t=prior.extended_gcd(polynomial,cubic)
        assert common==row['gcd_coefficients_low_to_high']
        assert prior.add(prior.mul(s,polynomial),prior.mul(t,cubic))==common
        assert not any(prior.divide(polynomial,common)[1])
        assert not any(prior.divide(cubic,common)[1])
        roots=[x for x in range(P) if prior.horner(common,x)==0]
        bs=sorted([x,y] for x in roots for y in squares[(x**3-16)%P]
                  if x and (x**3-64)*pow(x*x,-1,P)%P==e[0]
                  and y*(x**3+128)*pow(x,-3,P)%P==e[1])
        assert bs==row['B_candidates']==[pair_by_key[pairkey]['B_point']]
    assert checked=={(*r['C_point'],*r['E_point']) for r in valid_rows}
    generated={}
    for shard in inverse['shards']:
        path=HERE/shard['file']
        assert sha256(path.read_bytes()).hexdigest()==shard['sha256']
        block=json.loads(path.read_text())
        assert len(block)==shard['rows']
        for row in block:
            triple=(*row['C_point'],*row['E_point'],*row['B_point'])
            assert triple not in generated
            generated[triple]={key(c) for c in row['chain_candidates']}
            assert len(generated[triple])==len(row['chain_candidates'])
    assert set(generated)==set(predicted)
    census=json.loads((HERE/'source_census.json').read_text())
    image=json.loads((HERE/'source_image.json').read_text())
    assert census['prime']==image['prime']==P and image['row_count']==census['paired_chain_count']==1384
    source_keys=[(tuple(r['curve_ainvs']),(i,j)) for r in census['rows'] for i in range(len(r['two_paths'])) for j in range(len(r['three_paths']))]
    image_keys=[key(r) for r in image['rows']]
    assert source_keys==image_keys and len(set(source_keys))==len(source_keys)
    cusps=sum(prior.phi(gcd(d,432//d)) for d in range(1,433) if 432%d==0 and (P-1)%gcd(d,432//d)==0)
    assert census['X0_point_count_from_Hecke']-cusps==len(source_keys)
    coord=json.loads(Path(inverse_protocol['inputs']['coordinate']['path']).read_text())
    intermediate=json.loads(Path(inverse_protocol['inputs']['intermediate']['path']).read_text())
    by_js=defaultdict(list)
    for c in coeffs_by_c:
        js=tuple(prior.j_value(record,c) for record in (coord['source_j'],intermediate['j3'],intermediate['j9'],coord['target_j']))
        by_js[js].append(c)
    models={(tuple(r['curve_ainvs']),r['label']):r for r in census['rows']}
    expected=defaultdict(set)
    for row in image['rows']:
        model=models[(tuple(row['source_ainvs']),row['source_label'])]
        i,j=row['pair']
        js=(model['j'],*(edge['target_j'] for edge in model['three_paths'][j]))
        assert len(by_js[js])==1 and len(row['B_candidates'])==1 and row['B_candidates'][0] is not None
        x,y=row['B_candidates'][0]
        e=((x**3-64)*pow(x*x,-1,P)%P,y*(x**3+128)*pow(x,-3,P)%P)
        triple=(*by_js[js][0],*e,x,y)
        assert key(row) not in expected[triple]
        expected[triple].add(key(row))
    missing=sorted(set(expected)-set(generated))
    extra=sorted(k for k in set(generated)-set(expected) if generated[k])
    wrong=sorted(k for k in set(expected)&set(generated) if expected[k]!=generated[k])
    assert not missing and not extra and not wrong
    assert len(generated)==len(predicted)==1376
    assert sum(map(len,expected.values()))==1384
    histogram=dict(sorted(Counter(len(expected.get(k,set())) for k in predicted).items()))
    assert histogram=={0:3,1:1362,2:11}
    prediction_path=HERE/'prediction_result.json'
    prediction=json.loads(prediction_path.read_text())
    assert prediction['status']=='FROZEN_P1367_J1728_27_PATH_PREDICTION'
    assert prediction['protocol_sha256']==sha256((HERE/'prediction_protocol.json').read_bytes()).hexdigest()
    assert prediction['source_code_sha256']==sha256((HERE/'predict_27_sage.py').read_bytes()).hexdigest()
    frozen={(*r['C_point'],*r['E_point'],*r['B_point']):r for r in prediction['predictions']}
    assert len(frozen)==7
    j1728_model=[r for r in census['rows'] if r['j']==1728%P]
    assert len(j1728_model)==1
    paths=j1728_model[0]['three_paths']
    path_counts=Counter(tuple([1728%P,*(edge['target_j'] for edge in path)]) for path in paths)
    assert [{'j_sequence':list(seq),'paths':n} for seq,n in sorted(path_counts.items())]==prediction['path_sequence_histogram']
    primary_mismatches=[]
    for triple,row in frozen.items():
        assert triple in predicted
        assert prior.j_value(coord['source_j'],triple[:2])==1728%P
        signature=tuple(prior.j_value(r,triple[:2]) for r in
                        (coord['source_j'],intermediate['j3'],intermediate['j9'],coord['target_j']))
        assert tuple(row['j_sequence'])==signature
        assert row['predicted_multiplicity']==path_counts[signature]
        observed=len(expected.get(triple,set()))
        if observed!=row['predicted_multiplicity']:
            primary_mismatches.append({'triple':list(triple),'predicted':row['predicted_multiplicity'],'observed':observed})
    assert not primary_mismatches
    assert Counter((r['predicted_multiplicity'],len(expected.get(k,set()))) for k,r in frozen.items())=={(0,0):3,(2,2):4}
    observed_primary_rows=[{'triple':list(triple),
                            'j_sequence':row['j_sequence'],
                            'predicted_multiplicity':row['predicted_multiplicity'],
                            'observed_multiplicity':len(expected.get(triple,set()))}
                           for triple,row in sorted(frozen.items())]
    jacobian_mismatches=sorted(k for k in predicted if (len(expected.get(k,set()))==2)!=predicted[k]
                                or len(expected.get(k,set())) not in (1,2))
    assert len(jacobian_mismatches)==7
    assert set(jacobian_mismatches)==set(frozen)
    assert len(inverse['jacobian_baseline_mismatches'])==7
    sieve=json.loads((HERE/'sieve_result.json').read_text())
    assert sieve['selected_prime']==P and len(sieve['cells'])==1
    assert sieve['cells'][0]['valid_triples']==7 and sieve['cells'][0]['distinct_valid_C_points']==2
    class_counts=Counter()
    for triple,critical in predicted.items():
        source_j=prior.j_value(coord['source_j'],triple[:2])
        source_class=('j0' if source_j==0 else 'j1728' if source_j==1728%P else 'generic')
        class_counts[(source_class,critical,len(expected.get(triple,set())),triple[5]==0)]+=1
    classes=[{'source_class':source_class,'predicted_double':critical,
              'observed_multiplicity':multiplicity,'sign_branch':sign_branch,'count':count}
             for (source_class,critical,multiplicity,sign_branch),count in sorted(class_counts.items())]
    assert sum(c['count'] for c in classes)==1376
    assert all((c['observed_multiplicity']==2)==c['predicted_double'] for c in classes if c['source_class']=='generic')
    out={'status':'PASS_P1367_INDEPENDENT_27_PATH_AUDIT','prime':P,
         'triples':len(generated),'source_chains':len(image['rows']),
         'primary_prediction_mismatches':primary_mismatches,'jacobian_baseline_mismatches':[list(k) for k in jacobian_mismatches],'missing_triples':missing,
         'extra_triples':extra,'wrong_candidate_sets':wrong,
         'integer_bezout_certificates':len(checked),'frozen_j1728_triples':len(frozen),
         'observed_primary_rows':observed_primary_rows,
         'candidate_count_histogram':histogram,
         'observed_classes':classes,
         'X0_rational_points_from_Hecke':census['X0_point_count_from_Hecke'],
         'rational_cusps':cusps,
         'source_census_sha256':sha256((HERE/'source_census.json').read_bytes()).hexdigest(),
         'source_image_sha256':sha256((HERE/'source_image.json').read_bytes()).hexdigest()}
    (HERE/'audit.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ('status','triples','source_chains','integer_bezout_certificates','candidate_count_histogram')},sort_keys=True))


if __name__=='__main__': main()
