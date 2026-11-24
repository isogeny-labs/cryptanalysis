\\ Compare common abscissae of y²=x³+2x±b for candidate b=1,...,1024.
\\ Emit only nonsingular models whose original cubic has no field root.
screen(p,b,verify) = {
  my(a=2,E,T,A,B,left,right,tA,tB,common,direct);
  E=ellinit([a,b],p);
  T=ellinit([a,-b],p);
  A=ellinit([0,2*a,0,a^2,-b^2],p);
  B=ellinit([0,a^2,0,-2*a*b^2,b^4],p);
  if (#E*#T*#A*#B==0, return());
  left=ellcard(E); right=ellcard(T);
  if (left%2==0, return());
  if (right%2==0 || left+right!=2*p+2, error("twist mismatch"));
  tA=ellap(A); tB=ellap(B);
  common=(p-1-tA-tB)/4;
  if (denominator(common)!=1, error("nonintegral overlap"));
  if (verify,
    direct=sum(x=0,p-1,issquare(Mod(x^3+a*x+b,p)) && issquare(Mod(x^3+a*x-b,p)));
    if (common!=direct, error("direct count mismatch"))
  );
  print(p,",",b,",",(left-1)/2,",",common,",",vecmax(factor(right)[,1]));
}
print("p,b,left_abscissae,common,largest_twist_prime");
forprime(q=7,251,if(q%4==3,for(b=1,min(q-1,30),screen(q,b,1))));
for(b=1,1024,screen(2^31-1,b,0));
