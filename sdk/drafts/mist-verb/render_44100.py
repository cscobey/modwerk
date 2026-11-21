#!/usr/bin/env python3
"""Offline 44.1k -> host SRC -> native 32k core -> host SRC -> 44.1k proof.

This does not run a 44.1 kHz native DSP effect or build instrument firmware.
"""
import argparse
import array
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import wave
from verify_src import compile_source

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('sdk', 'stock', 'assembler', 'host', 'disassembler', 'output'):
        parser.add_argument('--'+name, required=True, type=Path)
    args = parser.parse_args()
    out = args.output.resolve()
    if out == ROOT or ROOT in out.parents:
        parser.error('Output must be private, outside the module')
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, '-B', str(ROOT/'generate_src.py'), '--check'], check=True)
    compile_source('src_convert.cpp', out/'src_convert')
    rate = 44100
    # 160 ms pre-roll maps to exactly 5120 tank frames and exceeds clearing.
    pre = 7056
    frames = pre + 5*rate
    values = array.array('i')
    seed = 42
    for n in range(frames):
        t = n-pre
        seed = (1664525*seed+1013904223)&0xffffffff
        if 0 <= t < rate:
            decay = math.exp(-(t%11025)/600)
            l = .22 * decay * (seed/4294967296-.5)
            r = .10 * decay * math.sin(2*math.pi*733*t/rate)
        else:
            l = r = 0
        values.extend([round(l*8388608),round(r*8388608)])
    if sys.byteorder != 'little':
        values.byteswap()
    (out/'input-44100.raw').write_bytes(values.tobytes())
    def convert(direction, source, target):
        result = subprocess.run([str(out/'src_convert'),direction,str(source),str(target)],
                                capture_output=True,text=True,check=True)
        report = json.loads(result.stdout)
        if report['clippedSamples']:
            raise RuntimeError('SRC clipped the demonstration signal')
        return report
    down = convert('down', out/'input-44100.raw', out/'input-32000.raw')
    command = [sys.executable,'-B',str(ROOT/'render_core32.py')]
    for name in ('sdk','stock','assembler','host','disassembler'):
        command += ['--'+name,str(getattr(args,name))]
    command += ['--output',str(out/'native-core'),'--input-stereo',str(out/'input-32000.raw')]
    subprocess.run(command,check=True)
    up = convert('up', out/'native-core/wet.raw', out/'wet-44100.raw')
    if up['outputFrames'] != frames or down['outputFrames'] != frames*320//441:
        raise RuntimeError('Rate-conversion frame count mismatch')
    # Retain original bytes as a dry listening reference. This is not a test
    # of a native 44.1 kHz mixer; that implementation is still pending.
    (out/'dry-44100.raw').write_bytes((out/'input-44100.raw').read_bytes())
    for name in ('input','wet','dry'):
        samples = array.array('i'); samples.frombytes((out/(name+'-44100.raw')).read_bytes())
        if sys.byteorder != 'little':
            samples.byteswap()
        with wave.open(str(out/(name+'-44100.wav')),'wb') as wav:
            wav.setnchannels(2); wav.setsampwidth(3); wav.setframerate(rate)
            wav.writeframes(b''.join((v&0xffffff).to_bytes(3,'little') for v in samples))
    native = json.loads((out/'native-core/core-report.json').read_text())
    report = {'scope':'Offline host SRC around emulated 32 kHz core; no native 44.1 kHz effect or firmware',
              'inputFrames':frames,'asymmetricStereoInput':True,'down':down,'up':up,
              'nativeCore':native,
              'sourceHashes': {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
                               for name in ('rational_src.h','src_coefficients.h','render_44100.py')},
              'outputSha256':hashlib.sha256((out/'wet-44100.raw').read_bytes()).hexdigest()}
    (out/'pipeline-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
