#!/usr/bin/env python3
# Copyright 2026 cscobey. MIT; see LICENSE.
"""Probe new SRC address-register preservation on each core, privately."""
import argparse
import hashlib
import json
import re
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('assembler', 'host', 'native-render', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--inject-fault', action='store_true',
                        help='Positive control: corrupt n2 after each return; require detection')
    args = parser.parse_args()
    out, native = args.output.resolve(), args.native_render.resolve()
    if out == ROOT or ROOT in out.parents or out == native:
        parser.error('Use a separate private output folder')
    out.mkdir(parents=True, exist_ok=True)
    report = json.loads((native / 'report.json').read_text())
    assert report['reverb'] and not report['controlTrace'] and report['mix'] == 127
    for name, sha in report['sourceHashes'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == sha, name
    source, count = re.subn(r'^proc:$', 'engine_entry:',
                           (ROOT / 'core44100.asm').read_text(), flags=re.M)
    assert count == 1
    source += '''
proc:
        move #>$123456,n2
        move #>$654321,n3
        move #>$123456,r3
        move #>$7,m3
        move #>engine_entry,r4
        jsr (r4)
        move n2,a
        cmp #>$123456,a
        bne probe_failure
        move n3,a
        cmp #>$654321,a
        bne probe_failure
        move r3,a
        cmp #>$123456,a
        bne probe_failure
        move m3,a
        cmp #>$7,a
        bne probe_failure
        rts
probe_failure:
        move #>$bad,a
        move a1,x:(r7+$93)
        rts
'''
    if args.inject_fault:
        source = source.replace('        jsr (r4)\n        move n2,a',
                                '        jsr (r4)\n        move #>$0,n2\n        move n2,a')
    (out / 'registers.asm').write_text(source)
    subprocess.run([str(args.assembler), '-in', str(out / 'registers.asm'),
                    '-org', '15000', '-out', str(out / 'registers.bin'),
                    '-sym', str(out / 'registers.sym')], check=True)
    sym = {k: int(v, 16) for k, v in
           (line.split() for line in (out / 'registers.sym').read_text().splitlines())}
    blob = (out / 'registers.bin').read_bytes()
    words = [int.from_bytes(blob[i:i+3], 'little') for i in range(0, len(blob), 3)]
    assert words.count(0xfab1e0) == 1
    words[words.index(0xfab1e0)] = 0x14000
    assert 0x15000 + len(words) < 0x18000
    for core in 'AB':
        data = (native / (core + '.mem')).read_bytes()
        offset, result, replaced = 0, bytearray(), 0
        while offset + 9 <= len(data):
            space, start, length = struct.unpack_from('<BII', data, offset)
            offset += 9
            if space == 255:
                break
            values = data[offset:offset + length * 4]
            offset += length * 4
            if space == 0 and start == 0x15000:
                values = struct.pack('<' + 'I' * len(words), *words)
                length, replaced = len(words), replaced + 1
            result += struct.pack('<BII', space, start, length) + values
        assert replaced == 1
        (out / (core + '.mem')).write_bytes(result + struct.pack('<BII', 255, 0, 0))
    params = report['controls'][:3] + [0, report['controls'][3], 127] + [0] * 6
    params = ','.join(map(str, params))
    blocks = report['frames'] // 16
    for tracked in (0, 1):
        audio, track = out / f'audio{tracked}.raw', out / f'track{tracked}.txt'
        cmd = [str(args.host), '-mem', str(out / 'A.mem'), '-memB', str(out / 'B.mem'),
               '-init', format(sym['init'], 'x'), '-proc', format(sym['proc'], 'x'),
               '-inst', '2', '-core', '0,1', '-alloc', '1,1', '-r7', '2,2',
               '-audioidx', '0,0', '-frames', '16', '-blocks', str(blocks),
               '-in', str(native / 'input.raw') + ',' + str(native / 'input.raw'),
               '-split', str(report['split']), '-stereo', '-allocproc', 'end',
               '-audio', '0', '-guard', str(report['yExtentWords']), '-guard-shared',
               '-dirty', '1776', '-out', str(audio), '-trackout', str(track),
               '-track', '93', '-trackinst', str(tracked), '-params', params, '-params', params]
        run = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        (out / f'run{tracked}.log').write_text(run.stdout + run.stderr)
        if run.returncode:
            raise RuntimeError((run.stdout + run.stderr)[-2000:])
        rows = [list(map(int, line.split())) for line in track.read_text().splitlines()]
        expected = 0xbad if args.inject_fault else 0
        assert len(rows) == blocks and all(row[1] == expected for row in rows)
        for suffix in ('', '.i1'):
            assert Path(str(audio) + suffix).read_bytes() == Path(str(native / 'native.raw') + suffix).read_bytes()
    evidence = dict(scope='Private caller probe; not instrument ABI qualification',
                    sentinels=dict(n2='123456', n3='654321', r3='123456', m3='7'),
                    callsCheckedPerCore=blocks, trackedInstances=[0, 1],
                    faultInjected=args.inject_fault,
                    preservedOnBothCores=not args.inject_fault,
                    faultDetectedOnBothCores=args.inject_fault,
                    audioByteIdenticalOnBothCores=True,
                    sourceHashes={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                                  for name in ('core44100.asm', 'verify_registers.py')},
                    wrapperSourceSha256=hashlib.sha256(source.encode()).hexdigest())
    (out / 'report.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print(json.dumps(evidence, indent=2))


if __name__ == '__main__':
    main()
