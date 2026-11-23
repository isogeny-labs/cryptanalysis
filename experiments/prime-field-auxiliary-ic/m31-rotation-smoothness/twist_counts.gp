\\ Replay with gp -q -s 512M twist_counts.gp.
\\ Columns are neither, twist only, original only, both.
p = 2^31 - 1;
oddPrimes = [3,5,7,11,13,17,19,23,29,31,37,41,43,47];
bounds = [7,13,23,47];
orbitCounts = [652,4831,31857,239075];
expected = [[1331,1219,1220,1298],[9557,9208,9271,9381],[61985,61619,61577,61282],[463771,463698,462382,463016]];
seen = Map();
counts = vector(4);

{visit(v) =
  my(x=v, key=v);
  for(j=1,30, x=(2*x)%p; key=min(key,x));
  if(mapisdefined(seen,key), return());
  mapput(seen,key,1);
  if(kronecker(v,p)!=-1, return());
  x=v;
  for(j=1,31,
    if(kronecker(x*x+1,p)==-1,
      my(z=x^3+2*x, a=kronecker(z+14,p), b=kronecker(z-14,p));
      if(a*b==0, error("unexpected zero character"));
      counts[1+2*(a==1)+(b==1)]++);
    x=(2*x)%p);
}

{enumerate(v,first,bound) =
  visit(v);
  for(i=first,#oddPrimes,
    if(oddPrimes[i]>bound, break());
    if(v<=(p-1)\oddPrimes[i], enumerate(v*oddPrimes[i],i,bound)));
}

{iferr(for(i=1,#bounds,
  enumerate(1,1,bounds[i]);
  if(#seen!=orbitCounts[i] || counts!=expected[i], error("census mismatch at bound ",bounds[i]));
  print([bounds[i],#seen,counts])), err, print(err); quit(1))}
