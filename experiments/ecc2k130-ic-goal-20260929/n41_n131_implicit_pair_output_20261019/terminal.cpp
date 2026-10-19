// Target-conditioned S3 roots followed by table-free fixed-seed membership.
#define main archived_inverse_main
#include "../n131_w15_native_field_20261011/native_fast_sq.cpp"
#undef main

struct Basis {
    std::array<Fe,131> pivot{};
    std::array<uint32_t,131> masks{};
    void insert(Fe value,uint32_t mask) {
        while(!zero(value)) {
            int k=highbit(value);
            if(zero(pivot[k])){pivot[k]=value;masks[k]=mask;return;}
            value=xo(value,pivot[k]);mask^=masks[k];
        }
        throw std::runtime_error("dependent source-product basis");
    }
    bool decode(Fe value,uint32_t& mask)const{
        mask=0;
        while(!zero(value)){
            int k=highbit(value);
            if(zero(pivot[k]))return false;
            value=xo(value,pivot[k]);mask^=masks[k];
        }
        return true;
    }
};

static Fe halftrace(const Field& field,Fe value) {
    Fe result=value,power=value;
    for(int i=1;i<=(field.n-1)/2;++i){
        power=field.sq(field.sq(power));
        result=xo(result,power);
    }
    return result;
}

static std::vector<Fe> batch_inverse(const Field& field,const std::vector<Fe>& terms){
    const Fe one{1,0,0};
    std::vector<Fe> prefix(terms.size()+1),result(terms.size());
    prefix[0]=one;
    for(size_t i=0;i<terms.size();++i){
        if(zero(terms[i]))throw std::runtime_error("zero batch term");
        prefix[i+1]=field.mul(prefix[i],terms[i]);
    }
    Fe tail=field.inverse(prefix.back());
    for(size_t i=terms.size();i-->0;){
        result[i]=field.mul(tail,prefix[i]);
        tail=field.mul(tail,terms[i]);
    }
    if(!eq(tail,one))throw std::runtime_error("batch inversion replay");
    return result;
}

struct Left {Fe c;uint32_t code;};
struct Candidate {size_t left;Fe d;};

int main(int argc,char**argv){
try{
    if(argc!=2)throw std::runtime_error("usage: terminal terminal_n.txt");
    std::ifstream in(argv[1]);if(!in)throw std::runtime_error("input open failed");
    std::string tag,word;int n,d;size_t count;
    in>>tag>>n>>d;
    if(tag!="TERMINAL"||(n!=41&&n!=131)||d<=0||d>32)
        throw std::runtime_error("bad terminal header");
    in>>word;Fe C=decimal(word);
    in>>word;Fe H=decimal(word);
    in>>word;Fe target=decimal(word);
    in>>count;
    if(zero(C)||zero(H)||zero(target)||count==0||count>1000000)
        throw std::runtime_error("bad terminal parameters");
    Field field(n);Basis basis;
    for(int j=0;j<d;++j){
        in>>word;if(!in)throw std::runtime_error("missing basis");
        basis.insert(decimal(word),uint32_t(1)<<j);
    }
    std::vector<Left> left(count);
    for(auto& row:left){
        in>>word>>row.code;
        if(!in)throw std::runtime_error("missing left output");
        row.c=decimal(word);
        if(zero(row.c)||row.code>=(uint32_t(1)<<d))
            throw std::runtime_error("invalid left output");
    }
    in>>word;if(!in.eof())throw std::runtime_error("trailing terminal input");
    const Fe one{1,0,0};
    uint64_t start=ticks();
    std::vector<Fe> B(count),A(count),D(count),terms;
    std::vector<size_t> c_index(count),a_index(count,~size_t(0));
    terms.reserve(1+count*2);terms.push_back(target);
    for(size_t i=0;i<count;++i){
        B[i]=field.mul(left[i].c,target);
        A[i]=xo(one,field.sq(B[i]));
        D[i]=field.sq(xo(left[i].c,target));
        c_index[i]=terms.size();terms.push_back(left[i].c);
        if(!zero(A[i])){a_index[i]=terms.size();terms.push_back(A[i]);}
    }
    std::vector<Fe> inv=batch_inverse(field,terms);
    std::vector<Candidate> candidates;
    candidates.reserve(count*2);
    size_t trace_compatible=0,exceptional=0;
    for(size_t i=0;i<count;++i){
        Fe invB=field.mul(inv[c_index[i]],inv[0]);
        if(zero(A[i])){
            ++exceptional;
            Fe d=field.mul(D[i],invB);
            if(!zero(d))candidates.push_back({i,d});
            continue;
        }
        Fe q=field.mul(field.mul(A[i],D[i]),field.sq(invB));
        Fe h=halftrace(field,q);
        if(!eq(xo(field.sq(h),h),q))continue;
        ++trace_compatible;
        Fe scale=field.mul(B[i],inv[a_index[i]]);
        Fe first=field.mul(scale,h);
        Fe second=xo(first,scale);
        if(!zero(first))candidates.push_back({i,first});
        if(!zero(second))candidates.push_back({i,second});
    }
    std::vector<Fe> right_terms;
    right_terms.reserve(candidates.size());
    for(const auto& candidate:candidates)right_terms.push_back(candidate.d);
    std::vector<Fe> inv_right=batch_inverse(field,right_terms);
    size_t hits=0;
    for(size_t i=0;i<candidates.size();++i){
        const auto& row=candidates[i];
        Fe c=left[row.left].c,dval=row.d;
        Fe cd=field.mul(c,dval),cdt=field.mul(cd,target);
        Fe s3=xo(field.sq(xo(xo(c,dval),target)),
                 xo(cdt,field.sq(cdt)));
        if(!zero(s3))throw std::runtime_error("S3 replay mismatch");
        Fe p=field.mul(xo(field.mul(C,field.sq(dval)),H),inv_right[i]);
        uint32_t code=0;bool member=basis.decode(p,code);
        std::cout<<"ROOT "<<row.left<<" "<<left[row.left].code<<" ";
        write_fe(std::cout,c);std::cout<<" ";write_fe(std::cout,dval);
        std::cout<<" "<<(member?int64_t(code):-1)<<"\n";
        if(member){
            ++hits;
            std::cout<<"HIT "<<left[row.left].code<<" "<<code<<" ";
            write_fe(std::cout,c);std::cout<<" ";write_fe(std::cout,dval);
            std::cout<<" ";write_fe(std::cout,p);std::cout<<"\n";
        }
    }
    uint64_t elapsed=ticks()-start;
    std::cout<<"RESULT COMPLETE "<<n<<" "<<d<<" "<<count<<" "
             <<trace_compatible<<" "<<exceptional<<" "<<candidates.size()
             <<" "<<hits<<" "<<elapsed<<" "<<rss()<<"\n";
    return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}
}
