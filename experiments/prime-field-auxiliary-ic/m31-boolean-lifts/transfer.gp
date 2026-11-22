p=2^31-1; aux=ellinit([1,0],p); target=ellinit([2,14],p);
G=[Mod(3,p),Mod(615668188,p)]; K=ellmul(aux,G,2^26);
setrand(291159); seen=Map(); correct=0; lifts=0;
{
  while(#seen<4096,
    i=1+random(2^24-1);
    if(mapisdefined(seen,i),next);
    mapput(seen,i,1);
    R=ellmul(aux,G,2*i+1);
    for(k=1,32,
      x=lift(R[1]);
      key=bittest(x,5)+2*bittest(x,8)+4*bittest(x,15)+8*bittest(x,26);
      label=(#ellordinate(target,R[1])>0);
      lifts+=label;
      correct+=(label==bittest(10851,key));
      R=elladd(aux,R,K)));
}
print([#seen,correct,lifts]);
