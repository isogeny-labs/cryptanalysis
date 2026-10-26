"""Independent Horner replay of the exact B-image partition at p=997."""
import json
from collections import Counter,defaultdict
from hashlib import sha256
from pathlib import Path

HERE=Path(__file__).resolve().parent
P=997


def polynomial_by_e_power(terms):
    grouped=defaultdict(list)
    for term in terms:
        grouped[term['x_E_exponent']].append(term)
    return grouped


def horner(grouped,xc,yc,xe):
    top=max(grouped,default=0)
    value=0
    for exponent in range(top,-1,-1):
        coefficient=0
        for term in grouped.get(exponent,[]):
            coefficient += int(term['integer_coefficient'])*\
                pow(xc,term['x_C_exponent'],P)*pow(yc,term['y_C_exponent'],P)
        value=(value*xe+coefficient)%P
    return value


def main():
    protocol_path=HERE/'protocol.json'
    result_path=HERE/'result.json'
    fibers_path=HERE/'fibers.json'
    protocol=json.loads(protocol_path.read_text())
    result=json.loads(result_path.read_text())
    fibers=json.loads(fibers_path.read_text())
    assert sha256(fibers_path.read_bytes()).hexdigest()==result['fibers_sha256']
    assert fibers['protocol_sha256']==sha256(protocol_path.read_bytes()).hexdigest()
    inputs={name:json.loads(Path(record['path']).read_text())
            for name,record in protocol['inputs'].items()}
    for name,record in protocol['inputs'].items():
        assert sha256(Path(record['path']).read_bytes()).hexdigest()==record['sha256']
    source=inputs['paired_sources']['rows']
    image=inputs['isogeny_preimages']['rows']
    branch=inputs['branch']
    numer=polynomial_by_e_power(branch['numerator_terms'])
    denom=polynomial_by_e_power(branch['denominator_terms'])
    failures=[]
    seen=set()
    e_to_b=defaultdict(set)
    for row in fibers['fibers']:
        xb,yb=row['B_point']
        xe,ye=row['E_point']
        if (yb*yb-xb**3+16)%P or (xb**3-xe*xb**2-64)%P:
            failures.append({'B_point':[xb,yb],'reason':'B_or_isogeny_equation'})
        if (ye-yb*(xb**3+128)*pow(xb**3,-1,P))%P:
            failures.append({'B_point':[xb,yb],'reason':'isogeny_y'})
        e_to_b[(xe,ye)].add((xb,yb))
        for index in row['source_indices']:
            if index in seen or not 0<=index<len(source):
                failures.append({'index':index,'reason':'duplicate_or_invalid_index'})
                continue
            seen.add(index)
            prior=source[index]
            xc,yc=prior['C_point']
            if prior['E_point']!=[xe,ye]:
                failures.append({'index':index,'reason':'E_point_mismatch'})
                continue
            n=horner(numer,xc,yc,xe)
            d=horner(denom,xc,yc,xe)
            if not d or n!=d*xb%P:
                failures.append({'index':index,'reason':'Horner_branch_mismatch'})
        if len(row['source_indices'])!=row['size']:
            failures.append({'B_point':[xb,yb],'reason':'fiber_size_mismatch'})
    e_sizes=Counter()
    for row in image:
        for projection in row['projections']:
            e_sizes[tuple(projection['E_point'])]+=1
    e_allocation=[]
    for epoint,size in sorted(e_sizes.items()):
        occupied=e_to_b.get(epoint,set())
        fibers_here=[row['size'] for row in fibers['fibers']
                     if tuple(row['E_point'])==epoint]
        if size not in (12,24,48) or sum(fibers_here)!=size:
            failures.append({'E_point':list(epoint),'reason':'E_fiber_partition'})
        if (size,len(occupied),sorted(fibers_here)) not in (
                (12,1,[12]),(24,1,[24]),(48,2,[24,24])):
            failures.append({'E_point':list(epoint),'reason':'B_allocation_pattern',
                             'E_fiber_size':size,'B_fiber_sizes':fibers_here})
        e_allocation.append([size,len(occupied)])
    squares=Counter(y*y%P for y in range(P))
    order=1+sum(squares[(x*x*x-16)%P] for x in range(P))
    if order!=1008 or len(seen)!=1800:
        failures.append({'reason':'group_order_or_source_coverage','order':order,'seen':len(seen)})
    status=('PASS_INDEPENDENT_EXACT_B_IMAGE_AUDIT' if not failures and
            len(fibers['fibers'])==78 and result['full_B_image_including_identity']==79
            else 'FAIL_INDEPENDENT_EXACT_B_IMAGE_AUDIT')
    out={'status':status,'source_indices_covered':len(seen),
         'noncuspidal_B_image':len(fibers['fibers']),'B_group_order':order,
         'E_fiber_histogram':dict(Counter(e_sizes.values())),
         'B_fiber_histogram':dict(Counter(row['size'] for row in fibers['fibers'])),
         'E_to_B_occupancy_histogram':{f'{size}:{occupied}':count for (size,occupied),count
                                      in Counter(tuple(v) for v in e_allocation).items()},
         'failures':failures,'source_sha256':{'protocol':sha256(protocol_path.read_bytes()).hexdigest(),
                                            'result':sha256(result_path.read_bytes()).hexdigest(),
                                            'fibers':sha256(fibers_path.read_bytes()).hexdigest()}}
    (HERE/'audit.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ('status','source_indices_covered',
                                        'noncuspidal_B_image','B_group_order')},sort_keys=True))
    assert status=='PASS_INDEPENDENT_EXACT_B_IMAGE_AUDIT'


if __name__=='__main__':main()
