allocatemem(320000000);
p = 2^31-1;
aux = ellinit([1,0],p);
target = ellinit([2,14],p);
generator = [Mod(3,p), Mod(615668188,p)];
step = ellmul(aux,generator,2^26);
smooth = List([1]);
seen = Map();
hist = vector(33);
eligible = 0;
lifted = 0;
{
  foreach(primes([2,47]),q,
    oldSize = #smooth;
    for(i=1,oldSize,
      x = smooth[i];
      while(x <= (p-1)\q, x *= q; listput(smooth,x)));
    for(i=if(q==2,1,oldSize+1),#smooth,
      x = smooth[i];
      accepted = kronecker(x,p)==-1 && kronecker(x^2+1,p)==-1;
      if(q<=13,
        ys = ellordinate(aux,x);
        direct = #ys>0 && #ellmul(aux,[Mod(x,p),ys[1]],2^30)>1;
        if(direct!=accepted,error("order test mismatch")));
      if(!accepted,next);
      eligible++;
      lifted += (#ellordinate(target,x)>0);
      point = [Mod(x,p),ellordinate(aux,x)[1]];
      tag = lift(ellmul(aux,point,32)[1]);
      if(mapisdefined(seen,tag),next);
      mapput(seen,tag,1);
      h = 0;
      for(k=1,32,
        h += (#ellordinate(target,point[1])>0);
        if(k<32,point=elladd(aux,point,step)));
      hist[h+1]++);
    if(setsearch([2,3,7,13,31,47],q),
      print([q,#smooth,eligible,lifted,#seen,sum(k=1,33,(k-1)*hist[k]),sum(k=21,33,hist[k])]));
  );
  if([#smooth,eligible,lifted,#seen]!=[995969,249155,124093,247386],error("population mismatch"));
}
