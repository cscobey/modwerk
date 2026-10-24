// Copyright 2026 cscobey. MIT. Original algorithm: Emilie Gillet, MIT.
#include <algorithm>
#include <array>
#include <cmath>
#include <fstream>
#include <iostream>
#include <vector>
namespace clouds { struct FloatFrame { float l, r; }; }
#include "clouds/dsp/fx/reverb.h"
#include "clouds/dsp/fx/diffuser.h"
static clouds::Reverb reverb;
static clouds::Diffuser diffuser;
static std::array<uint16_t, 16384> tank;
static std::array<float, 2048> smear;
int main(int argc, char** argv) {
  if (argc != 9) return 2;
  std::ifstream input(argv[1], std::ios::binary | std::ios::ate);
  if (!input) return 3;
  auto bytes = input.tellg(); input.seekg(0);
  if (bytes < 0 || std::size_t(bytes) % sizeof(clouds::FloatFrame)) return 4;
  std::vector<clouds::FloatFrame> audio(std::size_t(bytes) / sizeof(clouds::FloatFrame));
  input.read(reinterpret_cast<char*>(audio.data()), bytes);
  if (!input) return 5;
  reverb.Init(tank.data()); diffuser.Init(smear.data());
  reverb.set_time(std::stof(argv[3])); reverb.set_diffusion(std::stof(argv[4]));
  reverb.set_lp(std::stof(argv[5])); reverb.set_input_gain(std::stof(argv[6]));
  reverb.set_amount(std::stof(argv[7])); diffuser.set_amount(std::stof(argv[8]));
  for (std::size_t n = 0; n < audio.size(); n += 32) {
    auto count = std::min<std::size_t>(32, audio.size() - n);
    diffuser.Process(audio.data() + n, count);
    reverb.Process(audio.data() + n, count);
  }
  std::ofstream output(argv[2], std::ios::binary);
  output.write(reinterpret_cast<const char*>(audio.data()), bytes);
  return output ? 0 : 6;
}
