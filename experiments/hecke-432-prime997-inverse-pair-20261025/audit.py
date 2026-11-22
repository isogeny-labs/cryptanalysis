"""Independent complete-field scan of resolvent pairs and kernel-chain joins."""
import json
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path

HERE=Path(__file__).resolve().parent
P=997


def curve_points(kind):
    square_roots=defaultdict(list)
    for y in range(P):
        square_roots[y*y%P].append(y)
    points=[]
    for x in range(P):
        rhs=(x*x*x+432)%P if kind=='E' else (4*(x*x*x-7)+1)%P
        for value in square_roots[rhs]:
            y=value if kind=='E' else (value-1)*pow(2,-1,P)%P
            points.append((x,y))
    return sorted(set(points))


def grouped_coefficients(terms,xc,yc):
    coefficients=[0]*13
    for t in terms:
        coefficients[t['x_E_exponent']]=(coefficients[t['x_E_exponent']]+int(t['integer_coefficient'])*
            pow(xc,t['x_C_exponent'],P)*pow(yc,t['y_C_exponent'],P))%P
    return coefficients


def horner(coefficients, x):
    value=0
    for coefficient in reversed(coefficients):
        value=(value*x+coefficient)%P
    return value


def branch_value(terms,xc,yc,xe):
    return sum(int(t['integer_coefficient'])*pow(xc,t['x_C_exponent'],P)*
               pow(yc,t['y_C_exponent'],P)*pow(xe,t['x_E_exponent'],P)
               for t in terms)%P


def main():
    protocol=json.loads((HERE/'protocol.json').read_text())
    inputs={}
    for name,record in protocol['inputs'].items():
        path=Path(record['path'])
        assert sha256(path.read_bytes()).hexdigest()==record['sha256']
        inputs[name]=json.loads(path.read_text())
    result=json.loads((HERE/'result.json').read_text())
    assert result['protocol_sha256']==sha256((HERE/'protocol.json').read_bytes()).hexdigest()
    pairs=[]
    for shard in result['pair_shards']:
        path=HERE/shard['file']
        assert sha256(path.read_bytes()).hexdigest()==shard['sha256']
        rows=json.loads(path.read_text())
        assert len(rows)==shard['rows']
        pairs.extend(rows)
    found={(tuple(row['C_point']),tuple(row['E_point'])):row for row in pairs}
    assert len(found)==len(pairs)
    c_points=curve_points('C')
    e_points=curve_points('E')
    assert len(c_points)+1==result['C_group_order']
    assert len(e_points)+1==result['E_group_order']
    e_by_x=defaultdict(list)
    for xe,ye in e_points:e_by_x[xe].append(ye)
    scan=set()
    for xc,yc in c_points:
        coefficients=grouped_coefficients(inputs['resolvent']['terms'],xc,yc)
        for xe,y_values in e_by_x.items():
            if horner(coefficients,xe)==0:
                for ye in y_values:scan.add(((xc,yc),(xe,ye)))
    assert scan==set(found)
    assert len(scan)==result['rational_pair_count']==1800
    sources=inputs['source_pairs']['rows']
    census={(tuple(row['curve_ainvs']),row['label']):row
            for row in inputs['source_census']['rows']}
    assert len(census)==len(inputs['source_census']['rows'])
    b_fibers=inputs['b_image']['fibers']
    expected_b={tuple(row['B_point']) for row in b_fibers}
    seen_source_indices=set()
    seen_b=set()
    chain_keys=set()
    failures=[]
    for pair,row in found.items():
        index=row['source_index']
        if index is None or index in seen_source_indices:
            failures.append({'pair':pair,'reason':'source_index'})
            continue
        seen_source_indices.add(index)
        source=sources[index]
        if tuple(source['C_point'])!=pair[0] or tuple(source['E_point'])!=pair[1]:
            failures.append({'pair':pair,'reason':'source_pair_mismatch'})
            continue
        key=(tuple(source['source_ainvs']),source['source_label'])
        chain=census[key]
        i,j=source['pair']
        if source['source_j']!=chain['j'] or source['terminal16_j']!=chain['two_paths'][i][-1]['target_j'] or source['terminal27_j']!=chain['three_paths'][j][-1]['target_j']:
            failures.append({'pair':pair,'reason':'kernel_chain_join'})
            continue
        chain_keys.add((key,i,j))
        xc,yc=pair[0]
        xe,ye=pair[1]
        n=branch_value(inputs['branch']['numerator_terms'],xc,yc,xe)
        d=branch_value(inputs['branch']['denominator_terms'],xc,yc,xe)
        if d==0:
            failures.append({'pair':pair,'reason':'branch_denominator'})
            continue
        xb=n*pow(d,-1,P)%P
        yden=(xb**3+128)%P
        if yden==0:
            failures.append({'pair':pair,'reason':'inverse_y_denominator'})
            continue
        yb=ye*pow(xb,3,P)*pow(yden,-1,P)%P
        if row['B_point']!=[xb,yb] or (xb,yb) not in expected_b or (yb*yb-xb**3+16)%P or (xb**3-xe*xb*xb-64)%P:
            failures.append({'pair':pair,'reason':'B_branch_or_image'})
            continue
        seen_b.add((xb,yb))
    assert len(seen_source_indices)==len(chain_keys)==1800
    assert seen_b==expected_b and len(seen_b)==78
    assert not failures
    audit={'status':'PASS_INDEPENDENT_FULL_FIELD_INVERSE_AUDIT',
           'C_affine_points':len(c_points),'E_affine_points':len(e_points),
           'rational_pairs_scanned':len(scan),'source_indices_joined':len(seen_source_indices),
           'distinct_chain_keys':len(chain_keys),'B_image_points':len(seen_b),
           'failures':failures,
           'method':'full C and E point tables; Horner at every rational E x; independent chain and branch replay'}
    (HERE/'audit.json').write_text(json.dumps(audit,sort_keys=True,indent=2)+'\n')
    print(json.dumps(audit,sort_keys=True))


if __name__=='__main__':main()
