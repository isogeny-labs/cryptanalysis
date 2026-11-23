p = 2^31-1;
g(x) = x^2-2;
f(x) = x^3+2*x+14;
tag(x) = kronecker(lift(f(x)),p);
doublex(x) = (3*x^2+2)^2/(4*f(x))-2*x;
iter(x,n) = {for(i=1,n,x=g(x)); x};
seedtrace = 0;
while(iter(Mod(seedtrace,p),30)!=-2,seedtrace++);
roots = polrootsmod(iter(x,7)-iter(Mod(seedtrace,p),7),p);
if(#roots!=128,error("fiber size"));
{
for(i=1,#roots,
  t=roots[i]; side=tag(t);
  if(!side,error("branch point"));
  for(j=1,32,t=doublex(t);if(tag(t)!=side,error("component changed")))
);
}
print("depth,images,base_images,twist_images,shared_images,twist_slots_with_square_image");
{
for(d=0,7,
  base=Set([]); twist=Set([]); hits=0;
  for(i=1,#roots,
    t=roots[i]; u=iter(t,d);
    if(tag(t)==1,base=setunion(base,[u]),twist=setunion(twist,[u]);hits+=(tag(u)==1))
  );
  print(d,",",#setunion(base,twist),",",#base,",",#twist,",",#setintersect(base,twist),",",hits)
);
}
