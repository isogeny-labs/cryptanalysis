int main(int argc,char** argv) {
  if (argc!=2) return 1;
  int run=std::atoi(argv[1]);
  Tables unused;
  unsigned count=0;
  auto ref=census(0,unused,count);
  if (ref.size()!=3846525 || count!=1924024) return 2;
  const int sequence[]={0,1,3,2};
  std::puts("run,round,position,arm,ms");
  for (int r=0;r<8;++r) for (int pos=0;pos<4;++pos) {
    int arm=(sequence[pos]+r+run)%4;
    auto start=std::chrono::steady_clock::now();
    auto out=census(arm<2 ? 1 : 2,unused,count);
    double ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();
    if (out!=ref || count!=1924024) return 3;
    std::printf("%d,%d,%d,%d,%.6f\n",run,r,pos,arm,ms);
  }
}
