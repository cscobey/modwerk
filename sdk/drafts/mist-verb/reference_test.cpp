// Copyright 2026 cscobey. MIT; see LICENSE.
// Executes the unchanged upstream reverb and a generated storage-only variant.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>
#include "packed16.h"
namespace clouds { struct FloatFrame { float l, r; }; }
#include "clouds/dsp/fx/reverb.h"
#include "clouds/dsp/fx/diffuser.h"
namespace clouds_packed { using FloatFrame = clouds::FloatFrame; }
#include "packed_reverb.h"
namespace clouds_lines { using FloatFrame = clouds::FloatFrame; }
#include "lines_reverb.h"

using Frame = clouds::FloatFrame;
using Audio = std::vector<Frame>;
constexpr int kRate = 32000;

void Require(bool condition, const char* message) {
  if (!condition) throw std::runtime_error(message);
}

void CheckStorage() {
  mist::Packed16<16384> buffer;
  std::array<uint16_t, 16384> reference{};
  uint32_t random = 0x4d495354;
  // Every signed 16-bit bit pattern, every residue, both end cells.
  for (unsigned v = 0; v < 65536; ++v) {
    for (unsigned i : {0u, 1u, 2u, 16381u, 16382u, 16383u}) {
      buffer.Write(i, uint16_t(v));
      reference[i] = uint16_t(v);
      for (unsigned j : {0u, 1u, 2u, 16381u, 16382u, 16383u})
        Require(buffer.Read(j) == reference[j], "packing changes a neighbour");
    }
  }
  for (int pass = 0; pass < 12; ++pass) {
    for (unsigned i = 0; i < reference.size(); ++i) {
      random = random * 1664525u + 1013904223u;
      auto cell = (pass & 1) ? 16383u - i : i;
      buffer.Write(cell, uint16_t(random >> 16));
      reference[cell] = uint16_t(random >> 16);
    }
    for (unsigned i = 0; i < reference.size(); ++i)
      Require(buffer.Read(i) == reference[i], "packed ring roundtrip fails");
    Require(buffer.ValidWords(), "physical word exceeds 24 bits");
  }
  buffer.Clear();
  for (unsigned i = 0; i < reference.size(); ++i)
    Require(buffer.Read(i) == 0, "packed ring clear fails");
  static_assert(mist::Packed16<16384>::kWords == 10924);
}

Audio Input(std::size_t count, unsigned seed) {
  Audio audio(count);
  for (std::size_t i = 0; i < count; ++i) {
    seed = seed * 1664525u + 1013904223u;
    float noise = (float(seed >> 8) / 16777216.0f - 0.5f);
    float envelope = std::exp(-float(i % 8000) / 350.0f);
    audio[i] = {noise * envelope * 0.5f,
      0.15f * std::sin(float(i) * 0.071f) * envelope};
  }
  return audio;
}

template<class Reverb>
Audio Render(const Audio& input, float time, float diffusion, float lp,
             float gain, float mix, float smear, int chunk) {
  // Upstream Init does not initialize the two scalar LP histories. Its module
  // uses static objects. Each render gets a fresh statically zero-initialized
  // object; do not rely on value initialization of its user-provided ctor.
  static Reverb pool[128];
  static std::size_t next = 0;
  Require(next < 128, "reference object pool exhausted");
  Reverb& reverb = pool[next++];
  std::array<uint16_t, 16384> tank{};
  clouds::Diffuser diffuser{};
  std::array<float, 2048> diffuser_memory{};
  reverb.Init(tank.data());
  diffuser.Init(diffuser_memory.data());
  reverb.set_time(time); reverb.set_diffusion(diffusion);
  reverb.set_lp(lp); reverb.set_input_gain(gain); reverb.set_amount(mix);
  diffuser.set_amount(smear);
  Audio result = input;
  for (std::size_t n = 0; n < result.size(); n += chunk) {
    auto size = std::min<std::size_t>(chunk, result.size() - n);
    diffuser.Process(result.data() + n, size);
    reverb.Process(result.data() + n, size);
  }
  return result;
}

void Write(const std::string& filename, const Audio& audio) {
  std::ofstream file(filename, std::ios::binary);
  file.write(reinterpret_cast<const char*>(audio.data()), audio.size() * sizeof(Frame));
  Require(file.good(), "cannot write audio");
}

int main(int argc, char** argv) {
  try {
    Require(argc == 2, "usage: reference_test OUTPUT_DIRECTORY");
    CheckStorage();
    std::cout << "PASS: lossless packing, neighbours, boundaries, clear, 24-bit words\n";
    const auto input = Input(64000, 17);
    int cases = 0;
    for (float time : {0.0f, 0.5f, 0.98f})
    for (float diffusion : {0.0f, 0.7f, 0.95f})
    for (float lp : {0.0f, 0.5f, 1.0f})
    for (float smear : {0.0f, 1.0f}) {
      auto a = Render<clouds::Reverb>(input, time, diffusion, lp, 0.2f, 1, smear, 32);
      auto b = Render<clouds_packed::Reverb>(input, time, diffusion, lp, 0.2f, 1, smear, 17);
      auto c = Render<clouds_lines::Reverb>(input, time, diffusion, lp, 0.2f, 1, smear, 31);
      for (std::size_t i = 0; i < input.size(); ++i) {
        Require(std::isfinite(a[i].l) && std::isfinite(a[i].r), "nonfinite output");
        if (a[i].l != b[i].l || a[i].r != b[i].r) {
          std::cerr << "case " << cases << ", sample " << i << ": "
                    << a[i].l << "," << a[i].r << " vs " << b[i].l << "," << b[i].r << '\n';
          throw std::runtime_error("packed output differs from upstream");
        }
        Require(a[i].l == c[i].l && a[i].r == c[i].r, "per-line output differs from upstream");
      }
      ++cases;
    }
    for (float gain : {0.0f, 0.2f, 1.0f})
    for (float mix : {0.0f, 0.5f, 1.0f}) {
      auto a = Render<clouds::Reverb>(input, .8f, .7f, .5f, gain, mix, 0, 32);
      auto b = Render<clouds_packed::Reverb>(input, .8f, .7f, .5f, gain, mix, 0, 1);
      auto c = Render<clouds_lines::Reverb>(input, .8f, .7f, .5f, gain, mix, 0, 13);
      for (std::size_t i = 0; i < input.size(); ++i) {
        Require(a[i].l == b[i].l && a[i].r == b[i].r, "gain/mix parity fails");
        Require(a[i].l == c[i].l && a[i].r == c[i].r, "per-line gain/mix parity fails");
      }
      ++cases;
    }
    Audio silence(64000);
    auto silent = Render<clouds::Reverb>(silence, .98f, .95f, 1, 1, 1, 1, 16);
    for (auto f : silent) Require(f.l == 0 && f.r == 0, "reference makes sound from silence");
    auto dry = Render<clouds::Reverb>(input, .8f, .7f, .5f, .2f, 0, 0, 16);
    for (std::size_t i = 0; i < input.size(); ++i)
      Require(dry[i].l == input[i].l && dry[i].r == input[i].r, "zero mix alters dry audio");
    auto demo = Input(kRate * 8, 42);
    for (std::size_t i = kRate * 2; i < demo.size(); ++i) demo[i] = {0, 0};
    Write(std::string(argv[1]) + "/dry.f32", demo);
    Write(std::string(argv[1]) + "/clouds-wet.f32",
      Render<clouds::Reverb>(demo, .85f, .7f, .5f, .2f, 1, 0, 32));
    Write(std::string(argv[1]) + "/clouds-smear.f32",
      Render<clouds::Reverb>(demo, .85f, .7f, .5f, .2f, 1, 1, 32));
    std::cout << "PASS: " << cases << " cases, two storage candidates exactly match upstream at 32000 Hz\n"
      << "PASS: initial silence, dry bypass; reference WAV inputs written\n";
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n'; return 1;
  }
}
