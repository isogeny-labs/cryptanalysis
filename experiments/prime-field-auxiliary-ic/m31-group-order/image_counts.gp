\\ Run with gp -fq -s 256M image_counts.gp </dev/null
\\ An x-coordinate represents the pair {P,-P}. The identity gets its own tag.
p = 2^31-1;
E = ellinit([2,14],p);

g = znprimroot(p)^((p-1)/126);

xs = Set(vector(126,j,lift(g^j)));
V = List();
for(i=1,#xs,ys=ellordinate(E,xs[i]);if(#ys,listput(V,[Mod(xs[i],p),ys[1]])));
V = Vec(V);

signed = [V,apply(P->ellneg(E,P),V)];
tag(P) = if(#P==1,-1,lift(P[1]));
pointcount(tags) = {
  my(s=vecsort(tags,,8));
  2*#s - (s[1]==-1)
};

\\ Fix the first sign positive since global negation preserves the tag.
\\ In sorted index order, opposite signs on a repeated index are detected
\\ at an adjacent pair. The unrestricted image includes these cancellations.
counts(m) = {
  my(n=#V,limit=2^(m-1)*binomial(n+m-1,m));
  my(alltags=vectorsmall(limit),eligible=vectorsmall(limit),na=0,ne=0);
  for(i=1,n,for(j=i,n,for(b=0,1,
    my(pair=elladd(E,V[i],signed[b+1][j]),pairOK=(i!=j || b==0));
    for(k=j,n,for(c=0,1,
      my(triple=elladd(E,pair,signed[c+1][k]),tripleOK=pairOK && (j!=k || b==c));
      if(m==3,
        na++;alltags[na]=tag(triple);
        if(tripleOK,ne++;eligible[ne]=alltags[na]),
        for(l=k,n,for(d=0,1,
          na++;alltags[na]=tag(elladd(E,triple,signed[d+1][l]));
          if(tripleOK && (k!=l || c==d),ne++;eligible[ne]=alltags[na])
        ))
      )
    ))
  )));
  if(na!=limit,error("incomplete enumeration"));
  [pointcount(alltags),pointcount(eligible[1..ne])]
};

verify() = {
  if(ellcard(E)!=2147505293 || znorder(g)!=126 || #V!=56,error("fixture mismatch"));
  for(m=3,4,
    actual=counts(m);
    expected=if(m==3,[234304,234192],[6557895,6551622]);
    if(actual!=expected,error("cardinality mismatch",m,actual));
    print(m," summands: unrestricted and eligible ",actual)
  )
};
iferr(verify(), err, print(err); quit(1));
