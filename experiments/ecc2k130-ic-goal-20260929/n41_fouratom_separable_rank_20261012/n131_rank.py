"""Challenge-field coefficient rank for archived W15 four-atom controls."""
import hashlib,json,resource,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'n131_w15_rotated_fouratom_inverse_20261010'
MOD=(1<<131)|(1<<13)|(1<<2)|(1<<1)|1
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def mul(a,b):
    out=0
    while b:
        if b&1:out^=a
        b>>=1;a<<=1
        if a>>131:a^=MOD
    return out
def power(a,k):
    out=1
    while k:
        if k&1:out=mul(out,a)
        a=mul(a,a);k>>=1
    return out
def frob(a,n):
    for _ in range(n):a=mul(a,a)
    return a
def coefficients(terms,a,b,z):
    aa=[power(a,i) for i in range(9)]
    bb=[power(b,i) for i in range(9)]
    zz=[power(z,i) for i in range(9)]
    M=[[0]*9 for _ in range(9)]
    for ia,ib,ip,iq,iz in terms:M[ip][iq]^=mul(mul(aa[ia],bb[ib]),zz[iz])
    return M
def rank(M):
    rows=[row[:] for row in M];r=0;pivots=[]
    for col in range(9):
        k=next((k for k in range(r,9) if rows[k][col]),None)
        if k is None:continue
        rows[r],rows[k]=rows[k],rows[r]
        pivot=rows[r][col];pivots.append([col,pivot])
        inverse=power(pivot,(1<<131)-2)
        assert mul(pivot,inverse)==1
        rows[r]=[mul(inverse,x) for x in rows[r]]
        for k in range(r+1,9):
            scalar=rows[k][col]
            if scalar:rows[k]=[x^mul(scalar,y) for x,y in zip(rows[k],rows[r])]
        r+=1
    return r,pivots
def main():
    start=time.monotonic_ns()
    protocol=json.loads((HERE/'protocol_n131.json').read_text())
    for name,path in [('source',Path(__file__)),('terms',BASE/'resultant.json'),
                      ('fixture',BASE/'control_result.json'),
                      ('positive',BASE/'input_n131_positive.txt'),
                      ('control',BASE/'input_n131_field_control.txt')]:
        assert sha(path)==protocol['sha256'][name],name
    terms=json.loads((BASE/'resultant.json').read_text())['terms']
    fixture=json.loads((BASE/'control_result.json').read_text())['n131']
    cases=[]
    for name in ('positive','control'):
        n,d,r0,r1,seed,z=map(int,(BASE/f'input_n131_{"positive" if name=="positive" else "field_control"}.txt').read_text().split())
        assert (n,d,r0,r1,seed)==(131,15,26,39,27372)
        a,b=fixture['rotated_seed_coordinates']
        assert fixture['seed_mask']*2==seed and fixture['pair_rotations']==[r0,r1]
        M=coefficients(terms,a,b,z)
        matrix_hash=hashlib.sha256(b''.join(x.to_bytes(17,'little') for row in M for x in row)).hexdigest()
        value,pivots=rank(M)
        cases.append({'case':name,'a':a,'b':b,'z':z,'rank':value,'pivots':pivots,
                      'nonzero_coefficients':sum(bool(x) for row in M for x in row),
                      'matrix_sha256':matrix_hash})
    result={'status':'EXACT_N131_COEFFICIENT_RANK','candidate_id':None,
            'protocol_sha256':sha(HERE/'protocol_n131.json'),'cases':cases,
            'elapsed_ns_exploratory':time.monotonic_ns()-start,
            'peak_rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (HERE/'result_n131.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(result['status'],[(c['case'],c['rank']) for c in cases])
if __name__=='__main__':main()
