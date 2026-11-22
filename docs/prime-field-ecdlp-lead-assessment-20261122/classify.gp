\\ S5 structural pre-screen for ECDLP over F_p. Coverage classifier (NOT a random-curve
\\ speed win): flags curves a generic rho/BSGS baseline must not be pointed at blind.
\\ Branches: anomalous (N==p), composite order (Pohlig-Hellman), small embedding degree
\\ (MOV/Frey-Ruck), j in {0,1728} (extra automorphisms).
classify(p,a,b)=
{
  if(Mod(4*a^3+27*b^2,p)==0, print("  p="p" a="a" b="b":  SINGULAR (skip)"); return(0));
  my(E=ellinit([a,b]*Mod(1,p)), N, t, fN, r, cof, j, k, flags=[]);
  N=ellcard(E); t=p+1-N; fN=factor(N); r=fN[matsize(fN)[1],1]; cof=N/r; j=lift(E.j);
  k=if(r>1,znorder(Mod(p,r)),0);
  if(N==p, flags=concat(flags,["ANOMALOUS (trace 1) -> Smart/SSS/Satoh-Araki, O(log p) LINEAR"]));
  if(!isprime(N), flags=concat(flags,[Str("COMPOSITE order (cofactor ",cof,") -> Pohlig-Hellman; run baseline in order-",r," subgroup")]));
  if(k>0 && k<=20, flags=concat(flags,[Str("small embedding degree k=",k," -> MOV/Frey-Ruck to F_p^",k)]));
  if(j==0 || j==1728, flags=concat(flags,[Str("j=",j," -> extra automorphisms, rho gains ~sqrt(|Aut/{+-1}|)")]));
  if(#flags==0, flags=["GENERIC (no cheap structural weakness; rho/BSGS is the instrument)"]);
  print("  p="p" a="a" b="b":  #E="N"  t="t"  j="j"  k="k);
  for(i=1,#flags, print("       - "flags[i]));
  return(1);
}
print("=== S5 structural pre-screen (demonstration) ===");
print("[1] small embedding degree / supersingular-type (p=23, a=1,b=0):"); classify(23,1,0);
print("[2] j=1728 family (b=0) over 31-bit prime:");  classify(2147483647,5,0);
print("[3] j=0 family (a=0) over 31-bit prime:");     classify(2147483647,0,7);
print("[4] composite-order curve:");                  classify(1000003,1,1);
