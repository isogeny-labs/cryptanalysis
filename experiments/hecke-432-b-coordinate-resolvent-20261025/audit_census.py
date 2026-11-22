"""Independently replay the rational branch on all 1,800 p=997 sources."""
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

HERE=Path(__file__).resolve().parent
MODULUS=997


def source_key(row):
    return (tuple(row['source_ainvs']),row['source_j'],row['source_label'],
            tuple(row['pair']))


def evaluate(terms,xc,yc,xe):
    return sum(int(row['integer_coefficient'])*pow(xc,row['x_C_exponent'],MODULUS)*
               pow(yc,row['y_C_exponent'],MODULUS)*pow(xe,row['x_E_exponent'],MODULUS)
               for row in terms)%MODULUS


def main():
    protocol_path=HERE/'census_protocol.json'
    protocol=json.loads(protocol_path.read_text())
    assert protocol['status']=='FROZEN_BEFORE_1800_ROW_BRANCH_AUDIT'
    inputs={}
    for name,record in protocol['inputs'].items():
        path=Path(record['path'])
        assert sha256(path.read_bytes()).hexdigest()==record['sha256']
        inputs[name]=json.loads(path.read_text())
    branch=inputs['branch']
    ce=inputs['source_CE']
    eb=inputs['source_EB']
    assert branch['status']=='EXPLICIT_RATIONAL_B_X_BRANCH'
    assert ce['source_count']==eb['row_count']==1800
    image={source_key(row):row for row in eb['rows']}
    assert len(image)==1800
    failures=[]
    selection=Counter()
    seen=0
    for row in ce['rows']:
        key=source_key(row)
        if key not in image:
            failures.append({'source_key':str(key),'reason':'missing_image_row'})
            continue
        cx,cy=row['C_point']
        ex,ey=row['E_point']
        assert (cy*cy+cy-cx**3+7)%MODULUS==0
        assert (ey*ey-ex**3-432)%MODULUS==0
        projections=[p for p in image[key]['projections'] if p['E_point']==[ex,ey]]
        if len(projections)!=1:
            failures.append({'source_key':str(key),'reason':'ambiguous_E_projection',
                             'count':len(projections)})
            continue
        n=evaluate(branch['numerator_terms'],cx,cy,ex)
        d=evaluate(branch['denominator_terms'],cx,cy,ex)
        if not d:
            failures.append({'source_key':str(key),'reason':'zero_branch_denominator'})
            continue
        xb=n*pow(d,-1,MODULUS)%MODULUS
        if not xb or (xb**3+128)%MODULUS==0:
            failures.append({'source_key':str(key),'reason':'undefined_isogeny_inverse',
                             'x_B':xb})
            continue
        yb=ey*pow(xb,3,MODULUS)*pow((xb**3+128)%MODULUS,-1,MODULUS)%MODULUS
        checks={'cubic':(xb**3-ex*xb**2-64)%MODULUS==0,
                'B_curve':(yb**2-xb**3+16)%MODULUS==0,
                'isogeny_y':(ey-yb*(xb**3+128)*pow(xb**3,-1,MODULUS))%MODULUS==0}
        options=projections[0]['B_preimages']
        if [xb,yb] not in options or not all(checks.values()):
            failures.append({'source_key':str(key),'reason':'branch_mismatch',
                             'B_point':[xb,yb],'checks':checks,'options':options})
            continue
        selection[options.index([xb,yb])]+=1
        seen+=1
    status=('PASS_1800_RATIONAL_B_BRANCH_AUDIT' if seen==1800 and not failures else
            'PARTIAL_1800_RATIONAL_B_BRANCH_AUDIT')
    out={'status':status,'source_records':1800,'verified_records':seen,
         'failures':failures,'selected_preimage_index_histogram':dict(selection),
         'protocol_sha256':sha256(protocol_path.read_bytes()).hexdigest()}
    (HERE/'census_verification.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ('status','source_records','verified_records',
                                        'selected_preimage_index_histogram')},sort_keys=True))
    assert status=='PASS_1800_RATIONAL_B_BRANCH_AUDIT'


if __name__=='__main__':main()
