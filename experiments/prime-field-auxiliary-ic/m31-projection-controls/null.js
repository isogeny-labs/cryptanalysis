"use strict";
const fs = require("node:fs");
const path = require("node:path");
const fixture = path.join(__dirname, "../snapshot/algebraic/optimized/results/field31_s5_base0/public.json");
const roots = JSON.parse(fs.readFileSync(fixture, "utf8")).structured_roots;
const partitions=[];
for(let a=0;a<31;a++)for(let b=0;b<a;b++)for(let c=0;c<b;c++)for(let d=0;d<c;d++){
  const mask=(1<<a)|(1<<b)|(1<<c)|(1<<d);
  const groups=new Map();
  roots.forEach((x,i)=>{const key=x&mask;groups.set(key,((groups.get(key)||0)|(1<<i))>>>0);});
  partitions.push([...groups.values()].map(bits=>({high:bits>>>24,low:bits&0xffffff,count:pop(bits)})));
}
function pop(x){
  x=x-((x>>>1)&0x55555555);
  x=(x&0x33333333)+((x>>>2)&0x33333333);
  return (((x+(x>>>4))&0x0f0f0f0f)*0x01010101)>>>24;
}
// Partition the 32-bit labeling space by eight high bits. The remaining
// 24 bits index the saturating counter for each labeling in this slice.
const visits=new Uint8Array(1<<24);
let onceOrMore=0,twiceOrMore=0,total=0;
for(let high=0;high<256;high++){
  visits.fill(0);
  for(const groups of partitions){
    let base=0, fixed=0, available=0, possible=true;
    const free=[];
    for(const g of groups){
      if(!g.high){free.push(g);available+=g.count;continue;}
      const bits=high&g.high;
      if(bits===g.high){base|=g.low;fixed+=g.count;}
      else if(bits){possible=false;break;}
    }
    if(!possible)continue;
    // A compatible labeling is constant on each projected key's bucket.
    // Each unforced bucket can contribute either zero or all its positive labels.
    function enumerate(i,need,remaining,low){
      if(need<0 || need>remaining)return;
      if(!need){
        if(visits[low]===0)onceOrMore++;
        if(visits[low]===1)twiceOrMore++;
        if(visits[low]<2)visits[low]++;
        total++;
        return;
      }
      const g=free[i];
      enumerate(i+1,need,remaining-g.count,low);
      enumerate(i+1,need-g.count,remaining-g.count,low|g.low);
    }
    enumerate(0,17-fixed,available,base);
  }
}
// Independent coefficient calculation counts incidences before deduplication.
let expected = 0;
for (const groups of partitions) {
  const counts = Array(18).fill(0);
  counts[0] = 1;
  for (const {count} of groups) {
    for (let n = 17; n >= count; n--) counts[n] += counts[n-count];
  }
  expected += counts[17];
}
if(total!==expected || expected!==53887730)throw Error("incidence count mismatch");
console.log({onceOrMore,twiceOrMore,total});
