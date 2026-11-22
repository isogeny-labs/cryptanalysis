
P = 2**31-1
def lift(x):
    return pow((x*x*x+2*x+14)%P,(P-1)//2,P) != P-1

def expand(x, positions):
    return sum(((x>>i)&1)<<j for i,j in enumerate(positions))

def spread(bits,n):
    return [bits[i*(len(bits)-1)//(n-1)] for i in range(n)]

def rank_witness(order):
    left=spread(order[:15],9)
    right=spread(order[15:],10)
    xs=[expand(i,left) for i in range(512)]
    ys=[expand(i,right) for i in range(544)]
    basis={}
    for x in xs:
        row=sum(int(lift(x|y))<<j for j,y in enumerate(ys))
        while row:
            pivot=row.bit_length()-1
            if pivot not in basis:
                basis[pivot]=row
                break
            row^=basis[pivot]
    return len(basis)

for name, order in [('low',list(range(31))),('high',list(reversed(range(31)))),
                    ('even-first',list(range(0,31,2))+list(range(1,31,2)))]:
    print(name,rank_witness(order),flush=True)
