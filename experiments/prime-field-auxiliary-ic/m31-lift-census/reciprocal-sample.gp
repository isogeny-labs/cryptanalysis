\\ Independent check against direct reciprocal evaluation in the field.
p = 2^31 - 1;
setrand(78531);
eligible = 0; mixed = 0;
{
  for(i = 1, 100000,
    x = 1 + random(p - 1);
    if(kronecker(x,p) != -1 || kronecker(x^2+1,p) != -1, next);
    X = Mod(x,p);
    Y = 1/X;
    t = lift(X+Y);
    signpair = kronecker(lift(X^3+2*X+14),p)*kronecker(lift(Y^3+2*Y+14),p);
    if(kronecker(t,p) != 1 || kronecker(t-2,p) != -1 || kronecker(t+2,p) != -1,
       error("selector mismatch"));
    if(kronecker(14*t^3+2*t^2-14*t+197,p) != signpair, error("product mismatch"));
    eligible++;
    mixed += (signpair == -1);
  );
}
print([eligible,mixed]);
