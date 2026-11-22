p = 2^31-1;
aux = ellinit([1,0],p);
target = ellinit([2,14],p);
G = [Mod(3,p),Mod(615668188,p)];
K = ellmul(aux,G,2^26);

coordinates(index) = {
  my(point=ellmul(aux,G,2*index+1), xs=vector(32));
  for(j=1,32,
    xs[j]=lift(point[1]);
    if(j<32, point=elladd(aux,point,K)));
  xs
};

score(xs) = sum(j=1,32,kronecker(xs[j]^3+2*xs[j]+14,p)>=0);

materialize(xs) = {
  my(points=List(), ys);
  for(j=1,32,
    ys=ellordinate(target,xs[j]);
    if(#ys,listput(points,[Mod(xs[j],p),ys[1]])));
  Vec(points)
};

used = Map();
nextIndex() = {
  my(i);
  until(!mapisdefined(used,i),i=random(2^24));
  mapput(used,i,1);
  i
};

bounded(i,t)={
 my(pt=ellmul(aux,G,2*i+1),xs=vector(32),miss=0,x);
 for(j=1,32,x=lift(pt[1]);xs[j]=x;
   if(kronecker(x^3+2*x+14,p)<0,miss++;if(miss>32-t,return([])));
   if(j<32,pt=elladd(aux,pt,K)));
 materialize(xs)
};
ordinary(i,t)={my(xs=coordinates(i));if(score(xs)<t,[],materialize(xs))};
setrand(291204);
batches=vector(24,b,vector(256,j,nextIndex()));
{
 for(b=1,#batches,for(k=1,3,
   t=[17,20,24][1+(b+k-2)%3];batch=batches[b];
   for(j=1,#batch,if(ordinary(batch[j],t)!=bounded(batch[j],t),quit(1)));
   for(pos=1,2,arm=(pos+b)%2;start=getwalltime();
     accepted=sum(j=1,#batch,if(arm,#bounded(batch[j],t)>0,#ordinary(batch[j],t)>0));
     print(b,",",t,",",arm,",",accepted,",",getwalltime()-start))));
}
