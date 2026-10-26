"""Assign every rational p=997 source to its exact optimal B image."""
import json
from collections import Counter,defaultdict
from hashlib import sha256
from pathlib import Path

HERE=Path(__file__).resolve().parent
P=997


def key(row):
    return (tuple(row['source_ainvs']),row['source_j'],row['source_label'],tuple(row['pair']))


def evaluate(terms,xc,yc,xe):
    return sum(int(t['integer_coefficient'])*pow(xc,t['x_C_exponent'],P)*
               pow(yc,t['y_C_exponent'],P)*pow(xe,t['x_E_exponent'],P)
               for t in terms)%P


def curve_order():
    count=1
    for x in range(P):
        rhs=(x*x*x-16)%P
        count += 1 if rhs==0 else (2 if pow(rhs,(P-1)//2,P)==1 else 0)
    return count


def main():
    protocol_path=HERE/'protocol.json'
    protocol=json.loads(protocol_path.read_text())
    assert protocol['status']=='FROZEN_BEFORE_EXACT_B_IMAGE_CENSUS'
    inputs={}
    for name,record in protocol['inputs'].items():
        path=Path(record['path'])
        assert sha256(path.read_bytes()).hexdigest()==record['sha256']
        inputs[name]=json.loads(path.read_text())
    branch=inputs['branch']
    source=inputs['paired_sources']
    image=inputs['isogeny_preimages']
    chain=inputs['chain_census']
    previous=inputs['branch_audit']
    assert branch['status']=='EXPLICIT_RATIONAL_B_X_BRANCH'
    assert source['source_count']==image['row_count']==1800
    assert chain['paired_chain_count']==1800
    assert previous['status']=='PASS_1800_RATIONAL_B_BRANCH_AUDIT'
    assert chain['X0_point_count_from_Hecke']-1800==protocol['expected_rational_cusps']
    assert curve_order()==protocol['expected_B_group_order']
    image_index={key(row):row for row in image['rows']}
    assert len(image_index)==1800
    fibers=defaultdict(list)
    e_for_b={}
    failures=[]
    ce_seen=set()
    for index,row in enumerate(source['rows']):
        source_key=key(row)
        if source_key not in image_index:
            failures.append({'index':index,'reason':'missing_source_projection'})
            continue
        xc,yc=row['C_point']
        xe,ye=row['E_point']
        if (yc*yc+yc-xc**3+7)%P or (ye*ye-xe**3-432)%P:
            failures.append({'index':index,'reason':'curve_equation'})
            continue
        ce_key=(xc,yc,xe,ye)
        if ce_key in ce_seen:
            failures.append({'index':index,'reason':'duplicate_CE_pair'})
            continue
        ce_seen.add(ce_key)
        n=evaluate(branch['numerator_terms'],xc,yc,xe)
        d=evaluate(branch['denominator_terms'],xc,yc,xe)
        if not d:
            failures.append({'index':index,'reason':'zero_branch_denominator'})
            continue
        xb=n*pow(d,-1,P)%P
        if not xb or (xb**3+128)%P==0:
            failures.append({'index':index,'reason':'undefined_isogeny_inverse'})
            continue
        yb=ye*pow(xb,3,P)*pow((xb**3+128)%P,-1,P)%P
        if (yb*yb-xb**3+16)%P or (xb**3-xe*xb*xb-64)%P:
            failures.append({'index':index,'reason':'B_or_isogeny_equation'})
            continue
        choices=[p for p in image_index[source_key]['projections'] if p['E_point']==[xe,ye]]
        if len(choices)!=1 or [xb,yb] not in choices[0]['B_preimages']:
            failures.append({'index':index,'reason':'independent_isogeny_preimage'})
            continue
        bpoint=(xb,yb)
        epoint=(xe,ye)
        if bpoint in e_for_b and e_for_b[bpoint]!=epoint:
            failures.append({'index':index,'reason':'B_image_maps_to_two_E_points'})
            continue
        e_for_b[bpoint]=epoint
        fibers[bpoint].append(index)
    rows=[{'B_point':list(point),'E_point':list(e_for_b[point]),
           'source_indices':indices,'size':len(indices)}
          for point,indices in sorted(fibers.items())]
    histogram=dict(sorted(Counter(row['size'] for row in rows).items()))
    e_to_b=defaultdict(set)
    for point,epoint in e_for_b.items():e_to_b[epoint].add(point)
    b_per_e=dict(sorted(Counter(len(points) for points in e_to_b.values()).items()))
    total=sum(row['size'] for row in rows)
    bound_ok=all(row['size']<=24 for row in rows)
    noncuspidal=len(rows)
    full=noncuspidal+1  # normalized rational cusps map to B identity
    order=curve_order()
    status=('PASS_EXACT_RATIONAL_B_IMAGE_CENSUS' if
            not failures and total==1800 and bound_ok and
            79<=full<=217 and len(e_to_b)==72 else
            'PARTIAL_EXACT_RATIONAL_B_IMAGE_CENSUS')
    full_receipt={'status':status,'prime':P,'fibers':rows,
                  'protocol_sha256':sha256(protocol_path.read_bytes()).hexdigest()}
    (HERE/'fibers.json').write_text(json.dumps(full_receipt,sort_keys=True,separators=(',',':'))+'\n')
    summary={'status':status,'prime':P,'rational_X0_points':chain['X0_point_count_from_Hecke'],
             'rational_cusps':protocol['expected_rational_cusps'],
             'noncuspidal_sources':1800,'assigned_sources':total,
             'noncuspidal_B_image':noncuspidal,'full_B_image_including_identity':full,
             'B_group_order':order,'B_points_outside_full_image':order-full,
             'B_fiber_size_histogram':histogram,
             'maximum_B_fiber_size':max(histogram,default=0),
             'E_image_count':len(e_to_b),'occupied_B_preimages_per_E_histogram':b_per_e,
             'failures':failures,'fibers_sha256':sha256((HERE/'fibers.json').read_bytes()).hexdigest(),
             'protocol_sha256':sha256(protocol_path.read_bytes()).hexdigest()}
    (HERE/'result.json').write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:summary[k] for k in ('status','assigned_sources','noncuspidal_B_image',
          'full_B_image_including_identity','B_points_outside_full_image',
          'B_fiber_size_histogram','occupied_B_preimages_per_E_histogram')},sort_keys=True))
    assert status=='PASS_EXACT_RATIONAL_B_IMAGE_CENSUS'


if __name__=='__main__':main()
