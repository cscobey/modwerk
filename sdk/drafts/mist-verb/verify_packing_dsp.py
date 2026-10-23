#!/usr/bin/env python3
"""Exercise the packing primitives on both emulated DSP cores, not the FX.

Requires this checkout's SDK, a patched dsp_host/dsp_asm/disassembler and the
developer's local MAIN OS. All stock-derived memory and results stay private.
"""
import argparse
import array
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def raw(path):
    data = array.array('i')
    data.frombytes(path.read_bytes())
    if sys.byteorder != 'little':
        data.byteswap()
    return data


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--sdk', required=True, type=Path)
    ap.add_argument('--stock', required=True, type=Path)
    ap.add_argument('--assembler', required=True, type=Path)
    ap.add_argument('--host', required=True, type=Path)
    ap.add_argument('--disassembler', required=True, type=Path)
    ap.add_argument('--output', required=True, type=Path)
    args = ap.parse_args()
    sdk, out = args.sdk.resolve(), args.output.resolve()
    if out == ROOT or ROOT in out.parents:
        ap.error('Output must be outside module source')
    out.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(sdk / 'tools/build'))
    from nolabelprefix import refuse_label_prefix
    refuse_label_prefix((ROOT / 'packed_probe.asm').read_text())
    subprocess.run([str(args.assembler), '-in', str(ROOT / 'packed_probe.asm'),
                    '-org', '15000', '-out', str(out / 'packing.bin'),
                    '-sym', str(out / 'packing.sym')], check=True)
    disassembly = subprocess.check_output([str(args.disassembler), '-in', str(out / 'packing.bin'),
                                          '-pc', '15000', '-le'], text=True)
    if re.search(r'\bmpysu\b|\brep\b|\binvalid\b', disassembly, re.I):
        raise RuntimeError('Unexpected multiply, uninterruptible REP or invalid instruction')
    (out / 'packing.disassembly.txt').write_text(disassembly)
    spec = importlib.util.spec_from_file_location('private_dsp_modmap', sdk / 'tools/build/dsp_modmap.py')
    modmap = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modmap)
    words = [int.from_bytes((out / 'packing.bin').read_bytes()[i:i+3], 'little')
             for i in range(0, (out / 'packing.bin').stat().st_size, 3)]
    original = args.stock.read_bytes()
    for core in 'AB':
        path = out / (core + '.mem')
        modmap.dumpmem(original, [core, str(path)])
        memory = path.read_bytes()
        offset = 0
        while offset + 9 <= len(memory):
            space, start, count = struct.unpack_from('<BII', memory, offset)
            if space == 0xff:
                break
            if space == 0 and start < 0x15000 + len(words) and start + count > 0x15000:
                raise RuntimeError('Probe overlaps stock P span')
            offset += 9 + count * 4
        path.write_bytes(memory[:offset] + struct.pack('<BII', 0, 0x15000, len(words)) +
                         struct.pack('<' + 'I' * len(words), *words) + struct.pack('<BII', 255, 0, 0))
    symbols = {line.split()[0]: int(line.split()[1], 16)
               for line in (out / 'packing.sym').read_text().splitlines()}
    count = 65536
    inputs = []
    for instance in range(8):
        values = array.array('i', ((n * 40503 + instance * 12347) & 65535 for n in range(count)))
        if sys.byteorder != 'little':
            values.byteswap()
        path = out / f'input-{instance}.raw'
        path.write_bytes(values.tobytes())
        inputs.append(path)
    cmd = [str(args.host), '-mem', str(out / 'A.mem'), '-memB', str(out / 'B.mem'),
           '-init', format(symbols['init'], 'x'), '-proc', format(symbols['proc'], 'x'),
           '-inst', '8', '-core', '0,0,0,0,1,1,1,1', '-alloc', '1,3,5,7,1,3,5,7',
           '-r7', '2,5,8,11,2,5,8,11', '-audioidx', '0,1,2,3,0,1,2,3',
           '-allocproc', 'end', '-frames', '16', '-blocks', str(count // 16),
           '-split', '0,1,7,15,0,1,7,15', '-guard', str(10924), '-guard-shared', '-dirty', '1776',
           '-in', ','.join(map(str, inputs)), '-out', str(out / 'output.raw'),
           '-meter', str(out / 'meter.txt'), '-audio', '0']
    run = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    (out / 'host.log').write_text(run.stdout + run.stderr)
    if run.returncode:
        raise RuntimeError('DSP host failed: ' + (run.stdout + run.stderr)[-2000:])
    for instance in range(8):
        path = Path(str(out / 'output.raw') + (f'.i{instance}' if instance else ''))
        rendered = raw(path)
        if len(rendered) != count * 2:
            raise RuntimeError('Truncated DSP output')
        for n in range(count):
            expected = (n * 40503 + instance * 12347) & 65535
            if rendered[2*n] != expected:
                raise RuntimeError(f'Current cell mismatch: instance {instance}, sample {n}: '
                                   f'{rendered[2*n]} != {expected}')
            if n and rendered[2*n+1] != ((expected - 40503) & 65535):
                raise RuntimeError(f'Previous cell corrupted: instance {instance}, sample {n}')
    meters = [[int(v) for v in row.split()] for row in (out / 'meter.txt').read_text().splitlines()]
    report = {'scope': 'Packing primitives only; not reverb/SRC/instrument qualification',
              'instances': 8, 'cores': 2, 'samplesPerInstance': count,
              'testedSplitOffsets': [0, 1, 7, 15], 'physicalBufferWords': 10924,
              'garbageInitialState': True, 'sharedAndInstanceGuards': True,
              'peakInstructionsPerCorePer16Frames': [max(row[k] for row in meters) for k in (1, 2)],
              'sourceSha256': hashlib.sha256((ROOT / 'packed_probe.asm').read_bytes()).hexdigest(),
              'command': cmd, 'result': 'passed'}
    (out / 'packing-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print('PASS: native packing, eight instances / both cores, all cell bit patterns, four ring wraps, '
          'split blocks, dirty state and memory guards')


if __name__ == '__main__':
    main()
