"""Independent integer-field replay of source-product ANF support."""
import hashlib,json,time
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
TERMS=json.loads((ROOT/'n131_w15_rotated_fouratom_inverse_20261010/resultant.json').read_text())['terms']

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def multiply(a,b,n,low):
    raw=0
    while b:
        if b&1:raw^=a
        a<<=1;b>>=1
    while raw.bit_length()>n:
        raw^=((1<<n)|low)<<(raw.bit_length()-n-1)
    return raw
def square(a,n,low):return multiply(a,a,n,low)
def frob(a,k,n,low):
    for _ in range(k):a=square(a,n,low)
    return a
def power(a,k,n,low):
    out=1
    while k:
        if k&1:out=multiply(out,a,n,low)
        a=square(a,n,low);k>>=1
    return out
def basis(n,d,s,rotation,low):
    pivots={};result=[]
    for i in range(1,d+1):
        w=1<<i
        value=frob(square(w,n,low)^multiply(s,w,n,low),rotation,n,low)
        remainder=value
        while remainder:
            p=remainder.bit_length()-1
            if p not in pivots:
                pivots[p]=remainder;result.append(value);break
            remainder^=pivots[p]
    assert len(result)==d-1
    return result
def boolean_product(a,b,n,low):
    out={}
    for ma,ca in a.items():
        for mb,cb in b.items():
            key=ma|mb
            out[key]=out.get(key,0)^multiply(ca,cb,n,low)
    return {k:v for k,v in out.items() if v}
def powers_of_linear(vectors,offset,n,low):
    squares=[{1<<(offset+i):value for i,value in enumerate(vectors)}]
    for _ in range(3):squares.append({mask:square(value,n,low) for mask,value in squares[-1].items()})
    out=[{0:1}]
    for exponent in range(1,9):
        value={0:1}
        for k in range(4):
            if exponent>>k&1:value=boolean_product(value,squares[k],n,low)
        out.append(value)
    return out
def matrix(a,b,z,n,low):
    ap=[power(a,k,n,low) for k in range(9)]
    bp=[power(b,k,n,low) for k in range(9)]
    zp=[power(z,k,n,low) for k in range(9)]
    M=[[0]*9 for _ in range(9)]
    for ia,ib,ip,iq,iz in TERMS:
        M[ip][iq]^=multiply(multiply(ap[ia],bp[ib],n,low),zp[iz],n,low)
    return M
def direct(M,p,q,n,low):
    pp=[power(p,k,n,low) for k in range(9)]
    qq=[power(q,k,n,low) for k in range(9)]
    value=0
    for i in range(9):
        for j in range(9):
            if M[i][j]:value^=multiply(M[i][j],multiply(pp[i],qq[j],n,low),n,low)
    return value
def build_anf(M,vp,vq,n,low):
    d=len(vp)
    pp=powers_of_linear(vp,0,n,low)
    qq=powers_of_linear(vq,d,n,low)
    out={}
    raw_count=0
    for i in range(9):
        for j in range(9):
            scalar=M[i][j]
            if not scalar:continue
            for pm,pc in pp[i].items():
                scaled=multiply(scalar,pc,n,low)
                for qm,qc in qq[j].items():
                    key=pm|qm
                    out[key]=out.get(key,0)^multiply(scaled,qc,n,low)
                    raw_count+=1
    out={k:v for k,v in out.items() if v}
    return out,raw_count
def eval_anf(anf,assignment):
    value=0
    for mask,coefficient in anf.items():
        if mask&assignment==mask:value^=coefficient
    return value
def main():
    started=time.monotonic()
    protocol=json.loads((HERE/'protocol.json').read_text())
    for name in protocol['cases']:
        assert sha(HERE/(name+'.txt'))==protocol['sha256'][name]
    cases=[]
    for name in ('n41_positive','n41_negative','n131_positive'):
        n,d,s0,s1,r0,r1,z,m0,m1,m2,m3=map(int,(HERE/(name+'.txt')).read_text().split())
        low=0x9 if n==41 else 0x2007
        seed0=s0<<1;seed1=s1<<1
        vp=basis(n,d,seed0,r0,low);vq=basis(n,d,seed1,r1,low)
        a=frob(seed0,r0,n,low);b=frob(seed1,r1,n,low)
        M=matrix(a,b,z,n,low)
        anf,raw=build_anf(M,vp,vq,n,low)
        histogram=[0]*35
        for mask in anf:histogram[bin(mask).count('1')]+=1
        prior=json.loads((HERE/(name+'.json')).read_text())
        assert len(anf)==prior['anf_monomials'] and raw==prior['raw_tensor_terms']
        assert histogram==prior['degree_histogram']
        p=frob(multiply(m0<<1,m1<<1,n,low),r0,n,low)
        q=frob(multiply(m2<<1,m3<<1,n,low),r1,n,low)
        assert (direct(M,p,q,n,low)==0)==prior['witness_anf_zero']
        zero_assignments=None
        if n==41:
            # Different algorithm: invert the complete 14-bit truth table by
            # Boolean Möbius transform and compare the resulting coefficients.
            table=[]
            for assignment in range(1<<(2*(d-1))):
                x=y=0
                for k in range(d-1):
                    if assignment>>k&1:x^=vp[k]
                    if assignment>>(d-1+k)&1:y^=vq[k]
                table.append(direct(M,x,y,n,low))
            zero_assignments=sum(value==0 for value in table)
            for k in range(2*(d-1)):
                bit=1<<k
                for mask in range(len(table)):
                    if mask&bit:table[mask]^=table[mask^bit]
            assert all(table[mask]==anf.get(mask,0) for mask in range(len(table)))
        cases.append({'case':name,'monomials':len(anf),'raw_tensor_terms':raw,
                      'degree_histogram':histogram,'positive_check':prior['witness_anf_zero'],
                      'complete_relaxed_zero_assignments':zero_assignments})
    out={'status':'PASS_INDEPENDENT_PRODUCT_ANF_REPLAY','cases':cases,
         'elapsed_s_exploratory':time.monotonic()-started,
         'protocol_sha256':sha(HERE/'protocol.json')}
    (HERE/'audit.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(out['status'],[(c['case'],c['monomials']) for c in cases],flush=True)
if __name__=='__main__':main()
