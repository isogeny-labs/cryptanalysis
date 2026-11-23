\\ Supply the frozen coordinate vector as xs before reading this file.
p = 2^31-1;
E = ellinit([2,14],p);
points = List();
for(i=1,#xs, my(x=xs[i], y); if(issquare(Mod(x^3+2*x+14,p),&y), listput(points,[Mod(x,p),y]); listput(points,[Mod(x,p),-y])));
if(#points != 1000, error("unexpected lift count"));


if(#polrootsmod(x^3+2*x+14,p),error("finite point fixed by negation"));
table(orbit)={
  my(n=#points, v=vector(if(orbit,n^2/4,n^2/2)),m=0,s);
  forstep(i=1,n,if(orbit,2,1),for(j=i,n,
    s=elladd(E,points[i],points[j]);
    if(#s==2,m++;v[m]=if(orbit,lift(s[1]),lift(s[1])*p+lift(s[2])))));
  if(m!=#v,error("wrong count"));
  Set(v)
};
a=table(0);b=table(1);
if(#a!=2*#b || Set(vector(#a,i,a[i]\p))!=b,error("sign-orbit coverage"));
print("distinct signed and unsigned ",[#a,#b]);
for(i=1,6,for(j=1,2,mode=(i+j)%2;gettime();t=getwalltime();v=table(mode);w=getwalltime()-t;c=gettime();print([i,mode,c,w,#v])));
