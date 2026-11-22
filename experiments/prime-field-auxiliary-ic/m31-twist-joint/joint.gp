p = 2^31-1;
cubictrace(q,b,c,d) = ellap(ellinit([0,b,0,c,d],q));
joint(q) = -cubictrace(q,4,4,-196)-cubictrace(q,4,-784,196^2)-1;
valid=0;
forprime(q=5,500,if(q==7 || (4*2^3+27*14^2)%q==0,next); if(sum(x=0,q-1,kronecker((x^3+2*x+14)*(x^3+2*x-14),q))!=joint(q),error("small prime check"));valid++);
print("small primes checked: ",valid);
a=-cubictrace(p,0,2,14); b=-cubictrace(p,0,2,-14); c=joint(p);
if((p+1+a)%2==0 || (p+1+b)%2==0,error("check zero lift terms"));
forstep(i=1,-1,-2,forstep(j=1,-1,-2,print([i,j,(p+i*a+j*b+i*j*c)/4])));
