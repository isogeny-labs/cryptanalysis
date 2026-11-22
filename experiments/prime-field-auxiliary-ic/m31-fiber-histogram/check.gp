p=2^31-1; E=ellinit([1,0],p); G=[Mod(3,p),Mod(615668188,p)]; K=ellmul(E,G,2^26);
{
  forstep(i=0,2^24-1,262147,
    R=ellmul(E,G,2*i+1); hits=0;
    for(j=1,32,x=lift(R[1]);hits+=(kronecker(x^3+2*x+14,p)>=0);R=elladd(E,R,K));
    print("check ",i," ",hits));
}
