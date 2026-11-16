// CT40: standalone exact-integer and modular-matrix projector checks.
// No producer Jacobian, elliptic or finite-field implementation imported.
// Only example companion modules are tested; the universal theorem is
// proved separately in CT40_LOCAL_TATE_SPLITTING.md.
// Research standing: [pcc:unverified].
const audit = function audit(){
  const f1=[101,7,1],f2=[101,11,1],error=(name)=>{throw Error(name)},must=(condition,name)=>{if(!condition)error(name)};
  const trim=a=>{a=a.slice();while(a.length>1&&a[a.length-1]===0)a.pop();return a};
  const add=(a,b)=>trim(Array.from({length:Math.max(a.length,b.length)},(_,i)=>(a[i]||0)+(b[i]||0)));
  const mul=(a,b)=>{let c=Array(a.length+b.length-1).fill(0);for(let i=0;i<a.length;i++)for(let j=0;j<b.length;j++)c[i+j]+=a[i]*b[j];return trim(c)};
  const sc=(a,k)=>trim(a.map(x=>k*x));
  const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
  const A=sc(mul([7,1],f2),-1),B=mul([11,1],f1),P=mul(f1,f2);
  must(eq(add(A,B),[404]),"Bezout");
  must(eq(mul(A,B),sc(mul(mul([7,1],[11,1]),P),-1)),"AB=-factor*P");
  must(eq(add(mul(A,A),sc(A,-404)),sc(mul(A,B),-1)),"A^2-404A");
  must(eq(add(mul(B,B),sc(B,-404)),sc(mul(A,B),-1)),"B^2-404B");
  const mod=(x,m)=>((x%m)+m)%m;
  const z=()=>Array.from({length:4},()=>Array(4).fill(0));
  const id=(m)=>Array.from({length:4},(_,i)=>Array.from({length:4},(_,j)=>+(i===j)%m));
  const madd=(a,b,m)=>a.map((row,i)=>row.map((v,j)=>mod(v+b[i][j],m)));
  const msm=(a,c,m)=>a.map(row=>row.map(v=>mod(v*c,m)));
  const mmul=(a,b,m)=>a.map(row=>Array.from({length:4},(_,j)=>mod(row.reduce((v,w,i)=>v+w*b[i][j],0),m)));
  const meq=(a,b)=>a.every((row,i)=>row.every((v,j)=>v===b[i][j]));
  function peval(a,F,m){let out=z();for(let i=a.length-1;i>=0;i--)out=madd(mmul(out,F,m),msm(id(m),a[i],m),m);return out}
  function inverse(n,m){let a=mod(n,m),b=m,x=1,y=0;while(b){let q=Math.floor(a/b);[a,b]=[b,a-q*b];[x,y]=[y,x-q*y]}must(a===1,"nonunit");return mod(x,m)}
  function matrix(m,t2=11){let F=z();F[0][1]=mod(-101,m);F[1][0]=1;F[1][1]=mod(-7,m);F[2][3]=mod(-101,m);F[3][2]=1;F[3][3]=mod(-t2,m);return F}
  const e1=[[1,0,0,0],[0,1,0,0],[0,0,0,0],[0,0,0,0]];
  const e2=[[0,0,0,0],[0,0,0,0],[0,0,1,0],[0,0,0,1]];
  let checks=0;
  for(let l of [3,5,7,11,13,17,19,23,29,31])for(let k=1;k<=3;k++){
    let m=l**k,F=matrix(m),u=inverse(404,m),E=msm(peval(A,F,m),u,m),G=msm(peval(B,F,m),u,m);
    must(meq(E,e1)&&meq(G,e2),`block ${l}^${k}`);
    must(meq(madd(E,G,m),id(m)),`sum ${l}^${k}`);
    must(meq(mmul(E,E,m),E)&&meq(mmul(G,G,m),G),`idempotence ${l}^${k}`);
    must(meq(mmul(E,G,m),z()),`orthogonality ${l}^${k}`);
    must(meq(mmul(F,E,m),mmul(E,F,m)),`Frobenius ${l}^${k}`);
    checks++;
  }
  let W=matrix(7,12),Ebad=msm(peval(A,W,7),inverse(404,7),7);
  must(!meq(mmul(Ebad,Ebad,7),Ebad),"wrong trace rejected");
  must(404%2===0 && 404%101===0,"exceptional primes");
  must(eq(f1.map(x=>mod(x,2)),f2.map(x=>mod(x,2))),"mod2 collision");
  must(f1[0]%101===0&&f2[0]%101===0,"mod101 collision");
  return {status:"PASS [pcc:unverified]",P,A,B,constant:404,primePowerTests:checks,exceptions:[2,101],negativeControl:"wrong trace 12 rejected"};
};
console.log(JSON.stringify(audit(),null,2));
