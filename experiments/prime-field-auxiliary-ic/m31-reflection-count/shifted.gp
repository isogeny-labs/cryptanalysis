cubic(t) = t^3 + 2*t + 14;
shifted(p,c) = {
  my(a=3*c^2-4, b=-3*c^4+84*c-4, d=cubic(c)^2);
  my(l=ellinit([0,a,0,-b,d],p), r=ellinit([0,b,0,a*d,-d^2],p));
  ellcard(l)+ellcard(r)-2*(p+1)-kronecker(-1,p)
};
verify_small() = {
  forprime(p=11,151,
    if(#polrootsmod(cubic(x),p)==0 && poldisc(cubic(x))%p,
      for(c=0,p-1,
        if(shifted(p,c)!=sum(z=0,p-1,kronecker(cubic(c+z)*cubic(c-z),p)),
          error("direct character sum mismatch",[p,c])))))
};
verify_small();
