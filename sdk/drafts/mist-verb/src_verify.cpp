// Copyright 2026 cscobey. MIT. Analytic tests for the host SRC reference.
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <string>
#include "rational_src.h"
using mist::Stereo24;
constexpr double kPi = 3.14159265358979323846;
std::map<std::string, double> metrics;
void Require(bool condition, const char* message) {
  if (!condition) throw std::runtime_error(message);
}
std::vector<Stereo24> Tone(int rate, double frequency) {
  std::vector<Stereo24> result(rate);
  for (int n = 0; n < rate; ++n)
    result[n].l = std::lround(.25 * 8388608 * std::sin(2*kPi*frequency*n/rate));
  return result;
}
double Amplitude(const std::vector<Stereo24>& signal, int rate, double frequency) {
  double re = 0, im = 0;
  const std::size_t begin = signal.size()/2, count = signal.size()-begin;
  for (std::size_t n = begin; n < signal.size(); ++n) {
    const double v = signal[n].l / 8388608.;
    re += v * std::cos(2*kPi*frequency*n/rate);
    im += v * std::sin(2*kPi*frequency*n/rate);
  }
  return 2*std::hypot(re,im)/count;
}
double Rms(const std::vector<Stereo24>& signal) {
  double energy = 0;
  const std::size_t begin = signal.size()/2;
  for (std::size_t n = begin; n < signal.size(); ++n) {
    double v = signal[n].l / 8388608.; energy += v*v;
  }
  return std::sqrt(energy/(signal.size()-begin));
}
double Residual(const std::vector<Stereo24>& signal, int rate, double frequency) {
  const std::size_t begin=signal.size()/2, count=signal.size()-begin;
  double cosine=0, sine=0, error=0;
  for(std::size_t n=begin;n<signal.size();++n) {
    const double phase=2*kPi*frequency*n/rate, value=signal[n].l/8388608.;
    cosine+=value*std::cos(phase);sine+=value*std::sin(phase);
  }
  cosine*=2./count;sine*=2./count;
  for(std::size_t n=begin;n<signal.size();++n) {
    const double phase=2*kPi*frequency*n/rate;
    const double difference=signal[n].l/8388608.-cosine*std::cos(phase)-sine*std::sin(phase);
    error+=difference*difference;
  }
  return std::sqrt(error/count);
}
double Db(double ratio) { return 20*std::log10(std::max(ratio,1e-15)); }
int main() {
 try {
  for (bool down : {true,false}) {
    const std::string prefix = down ? "down_" : "up_";
    mist::RationalSrc src(down);
    const int in = src.input_rate(), out = src.output_rate();
    // Independent channels, full-size and irregular streamed calls.
    std::vector<Stereo24> input(in), whole, chunks;
    uint32_t seed = 42;
    for (auto& frame : input) {
      seed=1664525*seed+1013904223; frame.l=int32_t(seed>>10)-2097152;
      seed=1664525*seed+1013904223; frame.r=int32_t(seed>>10)-2097152;
    }
    src.Process(input.data(),input.size(),whole);
    Require(whole.size()==std::size_t(out),"Exact one-second sample count failed");
    src.Reset();
    for (std::size_t n=0;n<input.size();) {
      seed=1664525*seed+1013904223;
      std::size_t count=std::min<std::size_t>(1+(seed%37),input.size()-n);
      src.Process(input.data()+n,count,chunks); n+=count;
    }
    Require(whole==chunks,"Chunk boundary changes output");
    Require(src.clipped()==0,"Unexpected clipping at test level");
    metrics[prefix+"chunk_bit_exact"]=1;
    src.Reset(); whole.clear();
    for(auto& frame:input) frame={1048576,-524288};
    src.Process(input.data(),input.size(),whole);
    for(std::size_t n=256;n<whole.size();++n)
      Require(whole[n]==Stereo24{1048576,-524288},"DC gain is not exact");
    metrics[prefix+"dc_exact"]=1;
    src.Reset(); whole.clear();
    for(auto& frame:input) frame={};
    src.Process(input.data(),input.size(),whole);
    for(auto frame:whole) Require(frame==Stereo24{},"Reset or silence failed");
    // Twenty consecutive seconds exercise the bounded rational clock and
    // history wrap. No float timing and no accumulated sample-count error.
    for(int second=1;second<20;++second) src.Process(input.data(),input.size(),whole);
    Require(whole.size()==std::size_t(out)*20,"Streaming count drift");
    metrics[prefix+"twenty_second_output_frames"]=double(whole.size());
    metrics[prefix+"delay_seconds"]=src.delay_seconds();
    for(int frequency:{100,1000,10000,13000}) {
      input=Tone(in,frequency); src.Reset(); whole.clear();
      src.Process(input.data(),input.size(),whole);
      double gain=Db(Amplitude(whole,out,frequency)/.25);
      metrics[prefix+"gain_db_"+std::to_string(frequency)]=gain;
      Require(std::abs(gain)<.1,"Passband gain outside 0.1 dB");
      for(auto frame:whole) Require(frame.r==0,"Stereo crosstalk");
      double residual=Db(Residual(whole,out,frequency)/(.25/std::sqrt(2.)));
      metrics[prefix+"residual_db_"+std::to_string(frequency)]=residual;
      Require(residual < -65,"Passband spurious energy exceeds -65 dB");
      if(!down && frequency>=10000) {
        double image=Db(Amplitude(whole,out,in-frequency)/.25);
        metrics[prefix+"image_db_"+std::to_string(frequency)]=image;
        Require(image < -70,"Interpolation image exceeds -70 dB");
      }
      for(auto& frame:input) { frame.r=frame.l;frame.l=0; }
      src.Reset();chunks.clear();src.Process(input.data(),input.size(),chunks);
      for(std::size_t n=0;n<whole.size();++n)
        Require(chunks[n].l==0 && chunks[n].r==whole[n].l,"Channel swap or isolation failed");
    }
    if(down) for(int frequency:{16000,17000,18000,20000,21000}) {
      input=Tone(in,frequency); src.Reset(); whole.clear();
      src.Process(input.data(),input.size(),whole);
      double alias=Db(Rms(whole)/(.25/std::sqrt(2.)));
      metrics[prefix+"alias_db_"+std::to_string(frequency)]=alias;
      Require(alias < -70,"Aliased output exceeds -70 dB");
    }
  }
  std::cout << std::setprecision(12) << "{\n";
  bool first=true;
  for(const auto& [key,value]:metrics) {
    if(!first)std::cout<<",\n";first=false;
    std::cout<<"  \""<<key<<"\": "<<value;
  }
  std::cout<<"\n}\n";
  return 0;
 } catch(const std::exception& e) {
  for(const auto& [key,value]:metrics)std::cerr<<key<<": "<<value<<'\n';
  std::cerr<<e.what()<<'\n';return 1;
 }
}
