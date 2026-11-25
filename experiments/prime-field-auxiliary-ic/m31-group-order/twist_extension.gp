p = 2^31-1;
N = ellcard(ellinit([2,14],p));
T = ellcard(ellinit([2,-14],p));
if (N != 2147505293 || T != 2147462003 || !isprime(N), error("curve orders"));
t = p+1-T;
A = Mod(1,N)*[0,-p;1,t];
M = znorder(Mod(-p,N));
if (M != 536876323 || znorder(Mod(-1,N)) != 2, error("root orders"));
dim(d) = 2-matrank(A^d-matid(2));
check(d) = if(dim(d) != (d%2==0)+(d%M==0), error("fixed-space mismatch at ",d));
for(d=1,512,check(d));
ds = [1,2,3,4,M-1,M,M+1,2*M-1,2*M,3*M];
for(i=1,#ds,check(ds[i]); print(ds[i],",",dim(ds[i])));
quit
