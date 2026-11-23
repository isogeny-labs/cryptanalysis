p=2^31-1;
iter(x,n)={for(i=1,n,x=x^2-2);x};
t=Mod(0,p);while(iter(t,30)!=-2,t++);
prev=Mod(2,p);cur=t; seen=Map();
bounds=[256,1024,4096];
print("odd_power,terminal,bound,base_smooth,base_other,twist_smooth,twist_other");
{
for(k=1,63,
  if(k%2,
    v=iter(cur,7);
    if(mapisdefined(seen,lift(v)),error("duplicate fiber")); mapput(seen,lift(v),1);
    rr=polrootsmod(iter(x,7)-v,p);
    if(#rr!=128,error("incomplete fiber"));
    count=matrix(3,4);
    for(i=1,128,
      u=rr[i];
      if(iter(u,30)!=-2,error("trace order mismatch"));
      side=kronecker(lift(u^3+2*u+14),p);
      if(!side || lift(u)<2,error("unexpected branch or unit"));
      fac=factor(lift(u)); largest=fac[matsize(fac)[1],1];
      for(j=1,3,col=1+(side==-1)*2+(largest>bounds[j]); count[j,col]++);
    );
    for(j=1,3,print(k,",",lift(v),",",bounds[j],",",count[j,1],",",count[j,2],",",count[j,3],",",count[j,4]));
  );
  nexttrace=t*cur-prev;prev=cur;cur=nexttrace;
);
}
