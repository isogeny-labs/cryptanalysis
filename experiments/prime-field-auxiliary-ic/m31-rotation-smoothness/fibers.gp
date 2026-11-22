p=2^31-1; aux=ellinit([1,0],p);
G=[Mod(3,p),Mod(615668188,p)]; K=ellmul(aux,G,2^26);
setrand(291191); seen=Map();
{
  while(#seen<8192,
    index=random(2^24);
    if(mapisdefined(seen,index),next);
    mapput(seen,index,1);
    R=ellmul(aux,G,2*index+1);
    for(j=1,32,
      x=lift(R[1]);
      print(#seen,",",index,",",x,",",kronecker(x^3+2*x+14,p)>=0);
      R=elladd(aux,R,K)));
}
