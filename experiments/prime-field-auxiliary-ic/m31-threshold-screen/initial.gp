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

choose(i,j,mode) = {
  my(xs=coordinates(i), ys);
  if(mode==1,return(xs));
  ys=if(mode==2,coordinates(j),-xs);
  if(score(ys)>score(xs),ys,xs)
};

used = Map();
nextIndex() = {
  my(i);
  until(!mapisdefined(used,i),i=random(2^24));
  mapput(used,i,1);
  i
};

qualify(i,j,m,t) = {
 my(xs=coordinates(i), n=score(xs));
 if(n<t && m!=1,xs=if(m==2,coordinates(j),-xs);n=score(xs));
 if(n<t,return(0));
 my(points=materialize(xs));
 if(#points!=n,error("count mismatch"));
 1
};
setrand(291143);
batches=vector(36,b,vector(256,j,[nextIndex(),nextIndex()]));
orders=[[1,2,3],[1,3,2],[2,3,1],[2,1,3],[3,1,2],[3,2,1]];
thresholds=[17,20,22,24];
{
 for(m=1,3,for(j=1,32,qualify(batches[1][j][1],batches[1][j][2],m,17)));
 for(b=1,#batches,for(k=1,4,
   t=thresholds[1+(k+b-2)%4]; batch=batches[b]; order=orders[1+(b-1)%6];
   for(q=1,3,m=order[q];gettime();start=getwalltime();
     n=sum(j=1,#batch,qualify(batch[j][1],batch[j][2],m,t));
     cpu=gettime();wall=getwalltime()-start;print(b,",",t,",",m,",",n,",",cpu,",",wall))));
}
