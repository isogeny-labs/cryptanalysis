// CT168 independent generic polynomial-reduction reference, no specialized field formulas.
#include <cstdint>
#include <cstdio>
#include <vector>
#include <stdexcept>
constexpr int p=223,q=p*p*p;
struct E { int v[3]; };
E decode(int x){ return {{x%p,(x/p)%p,x/(p*p)}}; }
int encode(E x){return x.v[0]+p*x.v[1]+p*p*x.v[2];}
E mul(E a,E b){
  int64_t a5[5]={0,0,0,0,0};
  for(int i=0;i<3;i++)for(int j=0;j<3;j++)a5[i+j]+=int64_t(a.v[i])*b.v[j];
  for(int k=4;k>=3;k--) a5[k-3]-=3*a5[k];
  E out{};for(int k=0;k<3;k++){int64_t t=a5[k]%p;out.v[k]=int(t<0?t+p:t);}return out;
}
E plus(E a,E b){E out{};for(int i=0;i<3;i++)out.v[i]=(a.v[i]+b.v[i])%p;return out;}
int main(){
  std::vector<uint8_t> res(q,0);
  for(int y=0;y<q;y++){E yy=decode(y);res[encode(mul(yy,yy))]=1;}
  int targets[3][3]={{9,0,0},{18,9,0},{18,9,1}};
  std::printf("{\"schema\":\"ct168-generic-independent-crosscheck-v1\",\"counts\":[");
  for(int j=0;j<3;j++){
    int64_t n=1,zero=0,nonzero_square=0;
    E B={{targets[j][0],targets[j][1],targets[j][2]}};
    for(int x=0;x<q;x++){
      E e=decode(x);E rhs=plus(mul(mul(e,e),e),B);
      if(encode(rhs)==0){n++;zero++;}
      else if(res[encode(rhs)]){n+=2;nonzero_square++;}
    }
    std::printf("%s{\"n\":%lld,\"zero\":%lld,\"nonzero_square\":%lld}",j?",":"",(long long)n,(long long)zero,(long long)nonzero_square);
  }
  std::puts("]}");
}
