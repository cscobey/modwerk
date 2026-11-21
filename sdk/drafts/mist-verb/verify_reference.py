#!/usr/bin/env python3
"""Check pinned source, compile unchanged Clouds, prove the packed host model.

No firmware, DSP emulator or external Python packages are used. Generated
headers/binaries/audio go only to the required --output directory outside Git.
This does not qualify a native module or establish fixed-point/SRC equivalence.
"""
import argparse
import array
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import wave

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if output == ROOT or ROOT in output.parents:
        parser.error('Output must be outside the module source folder')
    output.mkdir(parents=True, exist_ok=True)
    pins = json.loads((ROOT / 'sources.json').read_text())
    for item in pins['files']:
        actual = hashlib.sha256((ROOT / item['path']).read_bytes()).hexdigest()
        if actual != item['sha256']:
            raise RuntimeError('Pinned upstream source changed: ' + item['path'])
    # Generate a storage-only derivative in private scratch. All DSP arithmetic,
    # quantization, LFOs, delay lengths and sample order remain upstream's.
    engine = (ROOT / 'upstream/clouds/dsp/fx/fx_engine.h').read_text()
    engine = engine.replace('CLOUDS_DSP_FX_FX_ENGINE_H_', 'MIST_PACKED_FX_ENGINE_H_')
    engine = engine.replace('namespace clouds {', 'namespace clouds_packed {')
    engine = engine.replace('buffer_ = buffer;', 'buffer_ = &storage_;')
    engine = engine.replace('std::fill(&buffer_[0], &buffer_[size], 0);', 'buffer_->Clear();')
    engine = re.sub(r'buffer_\[(.*?)\]', r'(*buffer_)[\1]', engine, flags=re.S)
    engine = engine.replace('T* buffer_;', 'mist::Packed16<size>* buffer_;')
    engine = engine.replace('enum {\n    MASK', 'mist::Packed16<size> storage_;\n  enum {\n    MASK')
    engine = '#include "packed16.h"\n' + engine
    (output / 'packed_engine.h').write_text(engine)
    reverb = (ROOT / 'upstream/clouds/dsp/fx/reverb.h').read_text()
    reverb = reverb.replace('CLOUDS_DSP_FX_REVERB_H_', 'MIST_PACKED_REVERB_H_')
    reverb = reverb.replace('namespace clouds {', 'namespace clouds_packed {')
    reverb = reverb.replace('"clouds/dsp/fx/fx_engine.h"', '"packed_engine.h"')
    (output / 'packed_reverb.h').write_text(reverb)
    # A second candidate gives each logical delay its own circular head. This
    # removes the need to divide every arbitrary global-ring address by three
    # in the DSP version; head pointers can be advanced once per tank sample.
    lines = engine.replace('MIST_PACKED_FX_ENGINE_H_', 'MIST_LINES_FX_ENGINE_H_')
    lines = lines.replace('namespace clouds_packed {', 'namespace clouds_lines {')
    substitutions = {
        '(write_ptr_ + D::base + D::length - 1) & MASK': 'Index<D>(D::length - 1)',
        '(write_ptr_ + D::base + offset) & MASK': 'Index<D>(offset)',
        '(write_ptr_ + offset_integral + D::base + 1) & MASK': 'Index<D>(offset_integral + 1)',
        '(write_ptr_ + offset_integral + D::base) & MASK': 'Index<D>(offset_integral)',
    }
    for before, after in substitutions.items():
        if before not in lines:
            raise RuntimeError('Upstream layout changed: missing ' + before)
        lines = lines.replace(before, after)
    index_method = '''
    template<typename D>
    int32_t Index(int32_t offset) const {
      return D::base + (D::length - (sample_count_ % D::length) + offset) % D::length;
    }
'''
    lines = lines.replace('    DISALLOW_COPY_AND_ASSIGN(Context);',
                          index_method + '    DISALLOW_COPY_AND_ASSIGN(Context);')
    lines = lines.replace('int32_t write_ptr_;', 'int32_t write_ptr_;\n  uint32_t sample_count_;')
    lines = lines.replace('write_ptr_ = 0;', 'write_ptr_ = 0;\n    sample_count_ = 0;')
    lines = lines.replace('--write_ptr_;', '--write_ptr_;\n    ++sample_count_;')
    lines = lines.replace('c->write_ptr_ = write_ptr_;',
                          'c->write_ptr_ = write_ptr_;\n    c->sample_count_ = sample_count_;')
    (output / 'lines_engine.h').write_text(lines)
    (output / 'lines_reverb.h').write_text(
        reverb.replace('MIST_PACKED_REVERB_H_', 'MIST_LINES_REVERB_H_')
        .replace('namespace clouds_packed {', 'namespace clouds_lines {')
        .replace('"packed_engine.h"', '"lines_engine.h"'))
    command = [os.environ.get('CXX', 'c++'), '-std=c++17', '-O2', '-DTEST', '-fno-fast-math',
               '-ffp-contract=off', '-I' + str(ROOT), '-I' + str(ROOT / 'upstream'),
               '-I' + str(output), str(ROOT / 'reference_test.cpp'), '-o', str(output / 'reference-test')]
    if sys.platform == 'darwin':
        sdk = subprocess.check_output(['xcrun', '--show-sdk-path'], text=True).strip()
        command[1:1] = ['-isystem', sdk + '/usr/include/c++/v1']
    subprocess.run(command, check=True)
    result = subprocess.run([str(output / 'reference-test'), str(output)],
                            capture_output=True, text=True)
    if result.returncode:
        print(result.stdout, end='')
        print(result.stderr, file=sys.stderr, end='')
        raise SystemExit(result.returncode)
    print(result.stdout, end='')
    for name in ('dry', 'clouds-wet', 'clouds-smear'):
        audio = array.array('f')
        audio.frombytes((output / (name + '.f32')).read_bytes())
        if sys.byteorder != 'little':
            audio.byteswap()
        with wave.open(str(output / (name + '.wav')), 'wb') as wav:
            wav.setnchannels(2)
            wav.setsampwidth(2)
            wav.setframerate(32000)
            wav.writeframes(b''.join(struct.pack('<h', max(-32768, min(32767, round(v * 32767))))
                                     for v in audio))
    report = {'scope': 'Host reference and lossless buffer packing only; no native DSP executed',
              'eurorackRevision': pins['eurorack'], 'stmlibRevision': pins['stmlib'],
              'sampleRate': 32000, 'referenceCases': 63, 'storageCandidates': 2,
              'tank': {'logical16BitCells': 16384, 'physical24BitWords': 10924},
              'diffuser': {'proposed24BitWords': 2048, 'nativePrecision': 'not tested'},
              'proposedBufferWords': 12972, 'availableBeforeKeyWindow': 15870,
              'remainingWords': 2898, 'compileCommand': command,
              'results': result.stdout.splitlines(),
              'sourceHashes': {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
                               for name in ('reference_test.cpp', 'packed16.h', 'verify_reference.py')}}
    (output / 'reference-report.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
