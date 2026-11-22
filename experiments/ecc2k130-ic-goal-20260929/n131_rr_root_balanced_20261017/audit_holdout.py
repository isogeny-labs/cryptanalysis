"""Independent Gaussian and group replay of the prospective N131 holdout."""
import hashlib
import json
import time
from pathlib import Path

D=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    start=time.monotonic()
    source=json.loads((D/'holdout_source.json').read_text())
    result=json.loads((D/'holdout_result.json').read_text())
    protocol=json.loads((D/'eval_protocol.json').read_text())
    assert result['protocol_sha256']==sha(D/'eval_protocol.json')
    assert result['source_sha256']==sha(D/'holdout_source.json')
    assert all(sha(Path(path))==digest for path,digest in protocol['sources'].items())
    n=source['field_degree'];mod=source['field_modulus']
    assert n==131

    def mul(a,b):
        c=0
        while b:
            c^=a<<((b&-b).bit_length()-1)
            b&=b-1
        while c.bit_length()>n:
            c^=mod<<(c.bit_length()-n-1)
        return c

    def inv(a):
        assert a
        u,v,g,h=a,mod,1,0
        while u!=1:
            shift=u.bit_length()-v.bit_length()
            if shift<0:
                u,v,g,h=v,u,h,g
                shift=-shift
            u^=v<<shift;g^=h<<shift
        while g.bit_length()>n:
            g^=mod<<(g.bit_length()-n-1)
        return g

    def add(p,q):
        if p is None:return q
        if q is None:return p
        x,y=p;u,v=q
        if x==u:
            if y!=v or x==0:return None
            slope=x^mul(y,inv(x))
            xx=mul(slope,slope)^slope
            yy=mul(x,x)^mul(slope^1,xx)
        else:
            slope=mul(y^v,inv(x^u))
            xx=mul(slope,slope)^slope^x^u
            yy=mul(slope,x^xx)^xx^y
        return xx,yy

    def det(points):
        matrix=[]
        for x,y in points:
            x2=mul(x,x)
            matrix.append([1,x,y,x2,mul(x,y),mul(x2,x),mul(x2,y)])
        value=1
        for col in range(7):
            pivot=next((r for r in range(col,7) if matrix[r][col]),None)
            if pivot is None:return 0
            matrix[col],matrix[pivot]=matrix[pivot],matrix[col]
            top=matrix[col][col]
            value=mul(value,top)
            reciprocal=inv(top)
            for r in range(col+1,7):
                if matrix[r][col]:
                    scale=mul(matrix[r][col],reciprocal)
                    for c in range(col+1,7):
                        matrix[r][c]^=mul(scale,matrix[col][c])
                    matrix[r][col]=0
        return value

    checks=0;hits=0
    for root in (0,1):
        saved=result['rows'][root]
        assert saved['root']==root
        base=[tuple(source['roots'][root][0])]+[tuple(p) for p in source['fixed_points']]
        for sign in range(64):
            points=[(x,y^x if sign>>i&1 else y) for i,(x,y) in enumerate(base)]
            value=det(points+[(source['target'][0],source['target'][1]^source['target'][0])])
            assert value==saved['values'][sign]
            group=None
            for point in points:group=add(group,point)
            assert (value==0)==(group==tuple(source['target']))
            hits+=group==tuple(source['target'])
            checks+=1
    assert checks==128 and hits==0
    audit={'status':'PROSPECTIVE_N131_INDEPENDENT_AUDIT_PASS',
           'holdout_result_sha256':sha(D/'holdout_result.json'),
           'source_sha256':sha(D/'holdout_source.json'),
           'determinants_checked':checks,'group_sums_checked':checks,
           'group_hits':hits,'wall_s':time.monotonic()-start}
    (D/'holdout_audit_result.json').write_text(json.dumps(audit,sort_keys=True,indent=2)+'\n')
    print(json.dumps(audit,sort_keys=True))


if __name__=='__main__':
    main()
