p=2^31-1;
print("constant,group_order,point_order,cycle_length,cycles");
{
  forstep(b=-14,14,28,
    E=ellinit([2,b],p);
    group=ellgroup(E);
    if(#group!=1,error("expected cyclic group"));
    N=group[1];
    fordiv(N,d,if(d>1,
      k=znorder(Mod(2,d));
      s=if(k%2==0 && Mod(2,d)^(k/2)==-1,k/2,k);
      print(b,",",N,",",d,",",s,",",eulerphi(d)/(2*s))
    ))
  )
}
