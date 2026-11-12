'use strict';
// CT49 independent JS certificate; arithmetic in F101 and an explicit cubic extension.
// No native/Rust or Python checker code is imported. [pcc:unverified]
const P=101, Q=P*P, v=x=>(x%P+P)%P;
function ck(x,s){if(!x)throw Error(s);}
const fixture={
 Cpi1:{g:[3,26,3,1],f:[52,0,25,0,77,0,84],d:[50,51],targets:[[46,8,49,99,4,78,54],[46,93,49,2,4,23,54]]},
 Cpi2:{g:[3,-3,18,1],f:[72,0,85,0,14,0,93],d:[81,20],targets:[[77,81,100,16,0,40,71],[77,20,100,85,0,61,71]]},
 C10:{g:[-38,-16,7,1],f:[89,0,93,0,8,0,61],d:[73,28],targets:[[49,17,85,87,33,9,10],[49,84,85,14,33,92,10]]},
 C20:{g:[3,46,24,1],f:[40,0,45,0,75,0,18],d:[34,67],targets:[[25,98,69,38,52,39,76],[25,3,69,63,52,62,76]]}
};
function ordinaryMul(a,b){let z=Array(a.length+b.length-1).fill(0);for(let i=0;i<a.length;i++)for(let j=0;j<b.length;j++)z[i+j]=v(z[i+j]+a[i]*b[j]);return z;}
function evalFp(a,x){return a.reduceRight((n,c)=>v(n*x+c),0);}
function field(c){
 const z=[0,0,0], one=[1,0,0], t=[0,1,0], cc=n=>[v(n),0,0];
 const add=(a,b)=>a.map((x,i)=>v(x+b[i]));
 const sub=(a,b)=>a.map((x,i)=>v(x-b[i]));
 const neg=a=>a.map(x=>v(-x));
 const mul=(a,b)=>{
  const arr=[0,0,0,0,0];for(let i=0;i<3;i++)for(let j=0;j<3;j++)arr[i+j]=v(arr[i+j]+a[i]*b[j]);
  for(let i=4;i>=3;i--){const q=arr[i];for(let j=0;j<3;j++)arr[i-3+j]=v(arr[i-3+j]-q*c[j]);}
  return arr.slice(0,3);
 };
 const pow=(a,n)=>{let r=one;for(;n>0;n=Math.floor(n/2),a=mul(a,a))if(n%2)r=mul(r,a);return r;};
 const eq=(a,b)=>a.every((x,i)=>x===b[i]);
 const polynomialMul=(a,b)=>{let r=Array.from({length:a.length+b.length-1},()=>z);for(let i=0;i<a.length;i++)for(let j=0;j<b.length;j++)r[i+j]=add(r[i+j],mul(a[i],b[j]));return r;};
 const deriv=a=>a.slice(1).map((x,i)=>mul(cc(i+1),x));
 const bracket=(a,b)=>{let u=polynomialMul(deriv(a),b),w=polynomialMul(a,deriv(b));return u.map((x,i)=>sub(x,w[i]||z));};
 const det=(rows)=>{
  const [a,b,c]=rows, tr=(x,y,z)=>mul(mul(x,y),z);
  return sub(add(add(tr(a[0],b[1],c[2]),tr(a[1],b[2],c[0])),tr(a[2],b[0],c[1])),
             add(add(tr(a[2],b[1],c[0]),tr(a[1],b[0],c[2])),tr(a[0],b[2],c[1])));
 };
 return {z,one,t,cc,add,sub,neg,mul,pow,eq,polynomialMul,bracket,det};
}
const squares=new Set(Array.from({length:P},(_,x)=>v(x*x)));
function character(x){return x===0?0:squares.has(v(x))?1:-1;}
function gf2mul(a,b){return [v(a[0]*b[0]+2*a[1]*b[1]),v(a[0]*b[1]+a[1]*b[0])];}
function countCurve(f){
 const ev=z=>f.reduceRight((a,b)=>{const w=gf2mul(a,z);return [v(w[0]+b),w[1]];},[0,0]);
 let n1=1+character(f[6]),n2=2;
 for(let a=0;a<P;a++)n1+=1+character(ev([a,0])[0]);
 for(let a=0;a<P;a++)for(let b=0;b<P;b++){
  const z=ev([a,b]);n2+=1+character(v(z[0]*z[0]-2*z[1]*z[1]));
 }
 const s1=P+1-n1,s2=(n2-Q-1+s1*s1)/2;
 return [n1,n2,Q+1+s2-(P+1)*s1];
}
let total=0;
for(const [name,{g,f,d,targets}] of Object.entries(fixture)){
 const F=field(g),{t,one,z,neg,mul,pow,eq,add,cc,polynomialMul,bracket,det}=F;
 const gm=g.map(v), reflected=[v(-g[0]),v(g[1]),v(-g[2]),1];
 ck(ordinaryMul(gm,reflected).map(x=>v(x*f[6])).every((x,i)=>x===f[i]),name+' original factorization');
 ck(!Array.from({length:P},(_,x)=>x).some(x=>evalFp(gm,x)===0),name+' reducible cubic');
 const r=[t,pow(t,P),pow(t,P*P)];
 ck(eq(pow(t,P*P*P),t) && !eq(r[0],r[1]),name+' extension irreducible');
 for(let sh=1;sh<=2;sh++){
  const q=r.map((a,i)=>{const b=neg(r[(i+sh)%3]);return [mul(a,b),neg(add(a,b)),one];});
  for(let i=0;i<3;i++)for(let j=0;j<3;j++)ck(eq(pow(q[i][j],P),q[(i+1)%3][j]),'not Galois stable');
  const delta=det(q);ck(eq(delta,cc(d[sh-1])),name+' determinant');
  const h=q.map((_,i)=>bracket(q[(i+1)%3],q[(i+2)%3]));
  const numer=polynomialMul(polynomialMul(h[0],h[1]),h[2]);
  const norm=mul(cc(f[6]),pow(delta,3));
  const scalar=pow(norm,P*P*P-2);
  const image=numer.map(x=>mul(x,scalar));
  ck(image.every(x=>x[1]===0&&x[2]===0),name+' non-descending codomain');
  ck(image.slice(7).every(x=>eq(x,z)),name+' nonzero trailing terms');
  const coeff=image.slice(0,7).map(x=>x[0]);
  ck(JSON.stringify(coeff)===JSON.stringify(targets[sh-1]),name+' wrong target '+coeff);
  ck(JSON.stringify(countCurve(coeff))==='[120,10436,12317]',name+' wrong Weil polynomial');
  ck(v(coeff[6])!==0,name+' zero leading coefficient');
  console.log(name+' shift '+sh+' determinant '+delta[0]+' target '+coeff.join(',')+' #J=12317');
  total++;
 }
 ck(eq(det(r.map(x=>[neg(mul(x,x)),z,one])),z),name+' even-pair mutant not degenerate');
}
ck(total===8,'wrong target count');
console.log('PASS JS: 8 exact non-split Richelot codomain certificates and zeta matches');
