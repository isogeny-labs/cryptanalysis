\\ Supply the frozen coordinate vector as xs before reading this file.
p = 2^31-1;
E = ellinit([2,14],p);
points = List();
for(i=1,#xs, my(x=xs[i], y); if(issquare(Mod(x^3+2*x+14,p),&y), listput(points,[Mod(x,p),y]); listput(points,[Mod(x,p),-y])));
if(#points != 1000, error("unexpected lift count"));

census(drop, collect) = {
  my(ids=select(i -> !setsearch(drop,(i-1)\2), [1..#points]));
  my(n=#ids, v=vector(n*(n+1)/2), m=0, s, code, edges=Map(), pair, edge);
  for(i=1,n, for(j=i,n,
    s=elladd(E,points[ids[i]],points[ids[j]]);
    if(#s==2,
      code=lift(s[1])*p+lift(s[2]);
      m++;
      v[m]=code*2^20+(ids[i]-1)*1024+ids[j]-1)));
  v=vecsort(v[1..m]);
  my(distinct=m);
  for(i=2,m, if(v[i]\2^20 == v[i-1]\2^20,
    distinct--;
    if(collect,
      pair=vector(2,j,v[i-2+j]%2^20);
      edge=Set(concat(vector(2,j,[pair[j]\2048,(pair[j]%1024)\2])));
      if(#edge!=4, error("unexpected collision support"));
      mapput(edges,edge,if(mapisdefined(edges,edge),mapget(edges,edge),0)+1))));
  [m,distinct,Mat(edges)]
};
full=census([],1);
if(full[1]!=500000 || full[2]!=499940, error("full census"));
edges=full[3];
if(matsize(edges)!=[10,2],error("unexpected number of edges"));
degree=vector(500);
for(i=1,10,if(edges[i,2]!=6,error("multiplicity"));for(j=1,4,degree[1+edges[i,1][j]]++));
if(vecmax(degree)!=2 || #select(x->x==2,degree)!=1,error("unexpected intersections"));
hub=select(i->degree[i+1]==2,[0..499])[1];
drop=Set(concat([hub],vector(10,i,if(setsearch(edges[i,1],hub),hub,edges[i,1][1]))));
if(#drop!=9,error("witness size"));
one=census([hub],0); witness=census(drop,0);
if(one[1]!=498002 || one[2]!=497954 || witness[1]!=482162 || witness[2]!=482162,error("subset census"));
print("shared coordinate index ",hub,", x = ",lift(points[2*hub+1][1]));
print("deleted indices ",drop);
print("pairs and distinct finite sums ",[full[1..2],one[1..2],witness[1..2]]);
