#!/usr/bin/env python3
"""Compile and test the host sample-rate-conversion reference without firmware."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def compile_source(name, output, sanitize=False):
    command = [os.environ.get('CXX', 'c++'), '-std=c++17', '-O2', '-ffp-contract=off']
    if sys.platform == 'darwin':
        sdk = subprocess.check_output(['xcrun', '--show-sdk-path'], text=True).strip()
        command += ['-isystem', sdk + '/usr/include/c++/v1']
    if sanitize:
        command += ['-fsanitize=undefined', '-fno-sanitize-recover=all']
    subprocess.run(command + [str(ROOT/name), '-o', str(output)], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--sanitize', action='store_true')
    args = parser.parse_args()
    out = args.output.resolve()
    if out == ROOT or ROOT in out.parents:
        parser.error('Output must be private, outside the module')
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, '-B', str(ROOT/'generate_src.py'), '--check'], check=True)
    compile_source('src_verify.cpp', out/'src_verify', args.sanitize)
    compile_source('src_convert.cpp', out/'src_convert', args.sanitize)
    result = subprocess.run([str(out/'src_verify')], capture_output=True, text=True, check=True)
    report = {'scope': 'Host integer SRC reference only; not DSP timing, native SRC or firmware qualification',
              'sampleRates': [44100, 32000], 'fractionalPhases': 32,
              'taps': {'down': 96, 'up': 48}, 'cutoffHz': 14500,
              'coefficientWords': 33 * (96+48), 'coefficientFormat': 'signed Q23',
              'activeHistoryWordsPerStereoInstance': 2 * (96+48),
              'allocatedHostHistoryWords': 2 * (96+96),
              'undefinedBehaviorSanitizer': args.sanitize,
              'metrics': json.loads(result.stdout),
              'sourceHashes': {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
                               for name in ('generate_src.py', 'src_coefficients.h', 'rational_src.h',
                                            'src_verify.cpp', 'src_convert.cpp')}}
    (out/'src-report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
