"""Round-trip oriented public points through one terminal and six selector bits."""
import sys
from pathlib import Path

P = 2**31 - 1
HALF = (P+1)//2
KX, KY = 1965083199, 1854403464
STEPS = [(0,0,1),(2,6,8),(262150,786438,3145792),
         (135006214,403445766,562160130),(199756251,1939860868,1327400300)]

def encode(x,y):
    bits = int(y <= (-y)%P)
    for t,a,b in STEPS:
        u = (x-t)%P
        v = b*pow(u,-1,P)%P
        bits = 2*bits + int(u <= v)
        x = (u+a+v)%P
    return x,bits

def root(r):
    z = pow(r%P,(P+1)//4,P)
    if z*z%P != r%P:
        raise ValueError("invalid quotient fiber")
    return z

def decode(x,bits):
    for t,a,b in reversed(STEPS):
        s = (x-a)%P
        d = root(s*s-4*b)
        u,v = (s+d)*HALF%P,(s-d)*HALF%P
        x = (t+(min(u,v) if bits&1 else max(u,v)))%P
        bits >>= 1
    y = root(x**3+x)
    return x,(min(y,(-y)%P) if bits else max(y,(-y)%P))

def replay(path):
    data=[tuple(map(int,line.split())) for line in Path(path).read_text().splitlines()]
    assert len(data)==32768
    terminals=set()
    distinct_words={}
    for start in range(0,len(data),32):
        row=data[start:start+32]
        codes=set()
        words=set()
        for j,(x,bit) in enumerate(row):
            xn=row[(j+1)%32][0]
            y=(x**3+x+KY**2-(x-KX)**2*(xn+x+KX))*pow(2*KY,-1,P)%P
            assert y*y%P==(x**3+x)%P
            for v,delta in ((y,1),((-y)%P,-1)):
                terminal,bits=encode(x,v)
                assert decode(terminal,bits)==(x,v)
                codes.add((terminal,bits))
                words.add(tuple(row[(j+delta*k)%32][1] for k in range(32)))
        assert codes=={(terminal,b) for b in range(64)}
        assert terminal not in terminals
        terminals.add(terminal)
        distinct_words[len(words)]=distinct_words.get(len(words),0)+1
    print(Path(path).name,len(terminals),"terminals,",64*len(terminals),"point round trips,",distinct_words)

if __name__=="__main__":
    for path in sys.argv[1:]:
        replay(path)
