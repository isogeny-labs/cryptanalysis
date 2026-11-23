\\ Product of the two lift characters, summed over x.
reflection_sum(p) = {
  my(a = ellinit([0,-4,0,4,196],p), b = ellinit([0,-4,0,-784,-38416],p));
  ellcard(a) + ellcard(b) - 2*(p+1) - kronecker(-1,p)
}
f(x) = x^3+2*x+14;
forprime(p=11,251, if(poldisc(x^3-4*x^2+4*x+196)%p && poldisc(196*x^3-4*x^2-4*x-1)%p, if(reflection_sum(p)!=sum(i=0,p-1,kronecker(f(i)*f(-i),p)),error("small-prime mismatch",p))))
p=2^31-1;
if(#polrootsmod(f(x),p),error("zero label"))
s=reflection_sum(p);
print("correlation sum=",s," mixed pairs=",(p-s)/4)
