// Copyright 2026 cscobey. MIT. Private offline raw-audio SRC driver.
#include <fstream>
#include <iostream>
#include <string>
#include "rational_src.h"
int main(int argc,char** argv) {
 try {
  if(argc!=4 || (std::string(argv[1])!="down" && std::string(argv[1])!="up")) {
    std::cerr<<"Usage: src_convert down|up input-stereo-s24-in-i32.raw output.raw\n";
    return 2;
  }
  const uint32_t endian=1;
  if(*reinterpret_cast<const uint8_t*>(&endian)!=1)throw std::runtime_error("Little-endian host required");
  static_assert(sizeof(mist::Stereo24)==8);
  std::ifstream input(argv[2],std::ios::binary|std::ios::ate);
  if(!input)throw std::runtime_error("Cannot read input");
  auto bytes=input.tellg();input.seekg(0);
  if(bytes<0 || std::size_t(bytes)%sizeof(mist::Stereo24))throw std::runtime_error("Invalid stereo frame length");
  std::vector<mist::Stereo24> frames(std::size_t(bytes)/sizeof(mist::Stereo24)), output;
  input.read(reinterpret_cast<char*>(frames.data()),bytes);
  if(!input)throw std::runtime_error("Truncated input");
  mist::RationalSrc src(std::string(argv[1])=="down");
  output.reserve((frames.size()*src.output_rate()+src.input_rate()-1)/src.input_rate());
  for(std::size_t n=0;n<frames.size();n+=17)
    src.Process(frames.data()+n,std::min<std::size_t>(17,frames.size()-n),output);
  std::ofstream file(argv[3],std::ios::binary);
  file.write(reinterpret_cast<const char*>(output.data()),std::streamsize(output.size()*sizeof(mist::Stereo24)));
  if(!file)throw std::runtime_error("Cannot write output");
  std::cout<<"{\"inputFrames\":"<<frames.size()<<",\"outputFrames\":"<<output.size()
           <<",\"clippedSamples\":"<<src.clipped()<<",\"delaySeconds\":"<<src.delay_seconds()<<"}\n";
  return 0;
 } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
