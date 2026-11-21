// Copyright 2026 cscobey. MIT.
// Compare the native recurrence model against the unchanged upstream oscillator.
#include <cmath>
#include <cstdint>
#include <iostream>
#include "stmlib/dsp/cosine_oscillator.h"
int main() {
 bool pass=true;
 for (int k=0;k<2;++k) {
  float frequency=(k ? .3f : .5f)/32000.f*32.f;
  stmlib::CosineOscillator oscillator;
  oscillator.Init<stmlib::COSINE_OSCILLATOR_APPROXIMATE>(frequency);
  int epsilon=k?25:67;
  int64_t y0=int64_t(0x400000)<<24;
  int64_t y1=y0-(int64_t(epsilon)<<22);
  double squared=0,peak=0; int peakTick=0;
  for(int n=0;n<5000;++n) {
   double original=oscillator.Next();
   double native=double(y0>>24)/8388608.+.5;
   double error=std::abs(original-native);
   squared+=error*error;
   if(error>peak){peak=error;peakTick=n;}
   int64_t next=2*y0-y1-2*(y0>>24)*epsilon;
   y1=y0;y0=next;
  }
  pass = pass && peak*(k?100:60) < .25;
  std::cout << (k?.3:.5) << " Hz: rms=" << std::sqrt(squared/5000) << " peak=" << peak << " at seconds=" << peakTick*.001 << " delay samples=" << peak*(k?100:60) << '\n';
 }
 return pass ? 0 : 1;
}
