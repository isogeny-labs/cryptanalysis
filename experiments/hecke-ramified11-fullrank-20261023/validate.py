"""Independent exact-rational replay of the full rank certificates."""
from collections import Counter
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREV = HERE.parent/'hecke-ramified11-fiber-20261023'
SOURCE = HERE.parent/'hecke-two-sheet-small-order-20261023'


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def rank_mod(rows, cols, q):
    a = [[int(row.get(str(j),0)) % q for j in cols] for row in rows]
    r = 0
    for j in range(len(cols)):
        pivot = next((k for k in range(r,len(a)) if a[k][j]),None)
        if pivot is None: continue
        a[r],a[pivot] = a[pivot],a[r]
        inv = pow(a[r][j],-1,q)
        a[r] = [(v*inv)%q for v in a[r]]
        for k in range(r+1,len(a)):
            if a[k][j]:
                factor = a[k][j]
                a[k] = [(v-factor*w)%q for v,w in zip(a[k],a[r])]
        r += 1
        if r == len(a): break
    return r


def combine(rows, terms):
    v = [Fraction(0) for _ in range(228)]
    for row_id, coeff_text in terms.items():
        coeff = Fraction(coeff_text)
        for col,value in rows[int(row_id)].items():
            v[int(col)] += coeff*value
    return v


def main():
    protocol = json.loads((HERE/'protocol.json').read_text())
    matrix = json.loads((HERE/'full_matrix.json').read_text())
    cert = json.loads((HERE/'certificates.json').read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_FULL_PRODUCER'
    assert matrix['protocol_sha256'] == digest(HERE/'protocol.json')
    assert matrix['source_sha256'] == protocol['source_sha256']['produce'] == digest(HERE/'produce.py')
    assert matrix['hecke11_sha256'] == protocol['source_sha256']['hecke11'] == digest(SOURCE/'tools/hecke11.py')
    assert protocol['source_sha256']['prior_walk'] == digest(PREV/'walk.json')
    assert protocol['source_sha256']['prior_fiber'] == digest(PREV/'fiber_gate_raw.json')
    assert protocol['prior_seal_sha256'] == digest(PREV/'SEAL.json')
    assert cert['full_matrix_sha256'] == digest(HERE/'full_matrix.json')
    assert cert['script_sha256'] == digest(HERE/'certify.py')
    points = matrix['column_points']; rows = matrix['relation_rows']; meta = matrix['row_records']
    assert (len(points),len(rows),len(meta)) == (228,190,190)
    assert [r['column'] for r in points] == list(range(228))
    assert len({tuple(r['point']) for r in points}) == 228
    assert dict(Counter(str(r['conductor']) for r in points)) == protocol['class_numbers']
    assert [r['row'] for r in meta] == list(range(190))
    expected_rows = {(1,2):38,(1,3):38,(2,3):38,(3,2):76}
    assert dict(Counter((r['conductor'],r['degree']) for r in meta)) == expected_rows
    assert matrix['rational_root_counts'] == {'2':{'1':114,'3':114},
                                              '3':{'1':152,'4':76}}
    assert matrix['hecke_eigenvalues'] == {'2':-2,'3':-1}
    c2 = cert['c2_row_ids']; others = cert['other_row_ids']
    assert len(c2)==38 and len(others)==152 and sorted(c2+others)==list(range(190))
    assert c2 == [r['row'] for r in meta if r['conductor']==2 and r['degree']==3]
    nonfloor = cert['nonfloor_column_ids']; floor = cert['floor_column_ids']
    assert nonfloor == [r['column'] for r in points if r['conductor']!=6]
    assert floor == [r['column'] for r in points if r['conductor']==6]
    assert len(nonfloor)==152 and len(floor)==76
    assert len(cert['c2_in_other_span_witnesses']) == 38
    row_for = {(r['source'],r['degree']):r['row'] for r in meta}
    assert len(row_for) == 190
    witness_by_row = {w['row']:w for w in cert['c2_in_other_span_witnesses']}
    local_commutator_sources = {}
    def neighbours(source,degree):
        row = rows[row_for[(source,degree)]]
        counts = {int(j):v for j,v in row.items()}
        counts[source] = counts.get(source,0) + matrix['hecke_eigenvalues'][str(degree)]
        return [j for j,n in counts.items() for _ in range(n) if n>0]
    for source in range(38):
        n2,n3 = neighbours(source,2),neighbours(source,3)
        assert len(n2)==3 and len(n3)==4
        c2_targets = [j for j in n2 if points[j]['conductor']==2]
        assert len(c2_targets)==1
        assert all(points[j]['conductor']==1 for j in n2 if j not in c2_targets)
        assert all(points[j]['conductor'] in (1,3) for j in n3)
        c2_row = row_for[(c2_targets[0],3)]
        predicted = Counter()
        for j in n3: predicted[row_for[(j,2)]] += 1
        predicted[row_for[(source,2)]] += 1
        for j in n2:
            if j != c2_targets[0]: predicted[row_for[(j,3)]] -= 1
        predicted[row_for[(source,3)]] -= 2
        predicted = {str(k):str(v) for k,v in predicted.items() if v}
        assert predicted == witness_by_row[c2_row]['terms'],(source,c2_row)
        local_commutator_sources[str(c2_row)] = source
    assert len(local_commutator_sources)==38
    for witness in cert['c2_in_other_span_witnesses']:
        assert witness['row'] in c2
        assert set(map(int,witness['terms'])) <= set(others)
        actual = combine(rows,witness['terms'])
        expected = [Fraction(rows[witness['row']].get(str(j),0)) for j in range(228)]
        assert actual == expected,witness['row']
    floor_vectors=[]
    assert len(cert['projected_other_kernel_witnesses']) == 2
    for witness in cert['projected_other_kernel_witnesses']:
        assert set(map(int,witness['terms'])) <= set(others)
        actual = combine(rows,witness['terms'])
        expected = [Fraction(witness['floor_vector'].get(str(j),0)) for j in range(228)]
        assert actual == expected
        assert all(actual[j]==0 for j in nonfloor)
        floor_vectors.append(actual)
    assert floor_vectors[0] != floor_vectors[1]
    nonzero_minor = any(floor_vectors[0][i]*floor_vectors[1][j] !=
                        floor_vectors[0][j]*floor_vectors[1][i]
                        for i in floor for j in floor if i<j)
    assert nonzero_minor
    c3_vertices = {r['column'] for r in points if r['conductor']==3}
    c3_adjacency = {}
    c3_to_floor = {}
    for source in sorted(c3_vertices):
        n2 = neighbours(source,2)
        horizontal = {j for j in n2 if points[j]['conductor']==3}
        descendants = [j for j in n2 if points[j]['conductor']==6]
        assert len(n2)==3 and len(horizontal)==2 and len(descendants)==1
        c3_adjacency[source]=horizontal
        c3_to_floor[source]=descendants[0]
    assert all(source in c3_adjacency[j] for source,ns in c3_adjacency.items() for j in ns)
    assert len(set(c3_to_floor.values())) == 76
    unseen=set(c3_vertices); c3_components=[]
    while unseen:
        stack=[min(unseen)]; comp=set()
        while stack:
            x=stack.pop()
            if x not in comp:
                comp.add(x); stack.extend(c3_adjacency[x]-comp)
        unseen-=comp; c3_components.append(comp)
    assert sorted(map(len,c3_components)) == [38,38]
    for witness,comp in zip(cert['projected_other_kernel_witnesses'],c3_components):
        signed_sources = {meta[int(row_id)]['source']:int(coeff)
                          for row_id,coeff in witness['terms'].items()}
        assert set(signed_sources)==comp
        assert set(signed_sources.values())=={-1,1}
        assert all(signed_sources[x] == -signed_sources[y]
                   for x in comp for y in c3_adjacency[x])
        assert {str(c3_to_floor[x]):str(sign) for x,sign in signed_sources.items()} == witness['floor_vector']
    mod_ranks={}
    for q in (101,1000000007,2147483647):
        other_rows=[rows[i] for i in others]
        mod_ranks[str(q)]={'others_full':rank_mod(other_rows,list(range(228)),q),
                           'others_nonfloor':rank_mod(other_rows,nonfloor,q),
                           'c2_full':rank_mod([rows[i] for i in c2],list(range(228)),q)}
        assert mod_ranks[str(q)] == {'others_full':152,'others_nonfloor':150,'c2_full':38}
    assert matrix['ranks'] == {
        'full_QQ':152,'nonfloor_QQ':150,
        'without_c2_full_QQ':152,'without_c2_nonfloor_QQ':150,
        'c2_full_QQ':38,'c2_nonfloor_QQ':38,
        'floor_only_row_directions':2,
        'c2_increment_full_QQ':0,'c2_increment_nonfloor_QQ':0}
    result={'status':'PASS_EXACT_FULL_MATRIX_RANK_CERTIFICATES',
            'protocol_sha256':digest(HERE/'protocol.json'),
            'full_matrix_sha256':digest(HERE/'full_matrix.json'),
            'certificates_sha256':digest(HERE/'certificates.json'),
            'validator_sha256':digest(HERE/'validate.py'),
            'verified_c2_row_combinations':38,
            'verified_local_hecke_commutator_explanations':len(local_commutator_sources),
            'verified_floor_only_vectors':2,
            'conductor3_degree2_cycle_lengths':sorted(map(len,c3_components)),
            'modular_rank_lower_bounds':mod_ranks,
            'certified_ranks':matrix['ranks'],
            'candidate_id':None,'timing_claim':None}
    (HERE/'validation.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:result[k] for k in ('status','verified_c2_row_combinations',
                                            'verified_floor_only_vectors','certified_ranks')},sort_keys=True))


if __name__=='__main__': main()
