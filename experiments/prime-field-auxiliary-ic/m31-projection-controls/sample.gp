p=2^31-1;E=ellinit([1,0],p);T=ellinit([2,14],p);G=[Mod(3,p),Mod(615668188,p)];K=ellmul(E,G,2^26);setrand(291160);seen=Map();count=0;
while(count<256,i=1+random(2^24-1);if(mapisdefined(seen,i),next);mapput(seen,i,1);R=ellmul(E,G,2*i+1);v=vector(32);h=0;for(k=1,32,x=lift(R[1]);y=(#ellordinate(T,x)>0);h+=y;v[k]=[x,y];R=elladd(E,R,K));if(h==17,count++;print(v)))
