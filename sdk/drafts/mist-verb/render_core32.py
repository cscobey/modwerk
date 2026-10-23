#!/usr/bin/env python3
"""Render the native 32 kHz tank experiment on both emulated cores.

This is not an instrument firmware or a 44.1 kHz effect. Measures discrepancy
against the unchanged float source instead of claiming bit-exact arithmetic.
"""
import argparse
import array
import hashlib
import importlib.util
import json
import math
import os
import re
from pathlib import Path
import struct
import subprocess
import sys
import wave

ROOT = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('sdk', 'stock', 'assembler', 'host', 'disassembler', 'output'):
        ap.add_argument('--' + name, required=True, type=Path)
    ap.add_argument('--controls', default='110,64,94,0,83',
                    help='TIME,DAMP,DIFF,SMEAR,GAIN, each 0..127; MIX tests 127 and 0')
    ap.add_argument('--split', type=int, default=0, choices=range(16),
                    help='Sub-block boundary, 0 for no split')
    ap.add_argument('--compare-output', type=Path,
                    help='Earlier render directory; require identical raw output on both cores')
    ap.add_argument('--input-stereo', type=Path,
                    help='Private 32 kHz signed-24-in-int32 stereo raw; whole 16-frame blocks')
    args = ap.parse_args()
    try:
        controls = [int(v) for v in args.controls.split(',')]
        if len(controls) != 5 or any(v < 0 or v > 127 for v in controls):
            raise ValueError
    except ValueError:
        ap.error('--controls requires five integers in 0..127')
    out = args.output.resolve()
    if ROOT == out or ROOT in out.parents:
        ap.error('Output must be private, outside the module')
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, '-B', str(ROOT/'generate_core.py'), '--check'], check=True)
    buffer_words = int(re.search(r'Y first (\d+) words', (ROOT/'core32.asm').read_text())[1])
    sys.path.insert(0, str(args.sdk/'tools/build'))
    from nolabelprefix import refuse_label_prefix
    refuse_label_prefix((ROOT/'core32.asm').read_text())
    subprocess.run([str(args.assembler), '-in', str(ROOT/'core32.asm'), '-org', '15000',
                    '-out', str(out/'core.bin'), '-sym', str(out/'core.sym')], check=True)
    listing = subprocess.check_output([str(args.disassembler), '-in', str(out/'core.bin'),
                                       '-pc', '15000', '-le'], text=True)
    if any(word in listing.lower() for word in ('mpysu', 'invalid', '\trep ')):
        raise RuntimeError('Unexpected opcode in core disassembly')
    (out/'core.disassembly.txt').write_text(listing)
    symbols = {s: int(v,16) for s,v in (row.split() for row in (out/'core.sym').read_text().splitlines())}
    table = [min(8388607, round(10**((-40 + 40*n/127)/20)*8388608)) for n in range(128)]
    blob = (out/'core.bin').read_bytes()
    words = [int.from_bytes(blob[i:i+3], 'little') for i in range(0,len(blob),3)]
    # Replace the declared module-table marker only in private assembled words.
    if words.count(0xfab1e0) != 1:
        raise RuntimeError('Gain table marker drift')
    words[words.index(0xfab1e0)] = 0x14000
    spec = importlib.util.spec_from_file_location('private_modmap', args.sdk/'tools/build/dsp_modmap.py')
    modmap = importlib.util.module_from_spec(spec); spec.loader.exec_module(modmap)
    original = args.stock.read_bytes()
    for core in 'AB':
        path = out/(core+'.mem'); modmap.dumpmem(original,[core,str(path)])
        data = path.read_bytes(); offset = 0
        while offset+9 <= len(data):
            space, start, count = struct.unpack_from('<BII',data,offset)
            if space == 255: break
            if space == 0:
                for address,length in [(0x14000,len(table)),(0x15000,len(words))]:
                    if start < address+length and start+count > address:
                        raise RuntimeError('Core or table overlaps original code')
            offset += 9+count*4
        data = data[:offset]
        for address,values in [(0x14000,table),(0x15000,words)]:
            data += struct.pack('<BII',0,address,len(values))+struct.pack('<'+'I'*len(values),*values)
        path.write_bytes(data+struct.pack('<BII',255,0,0))
    count = 4096+32000*5
    seed = 42; values = []
    for n in range(count):
        seed = (seed*1664525+1013904223)&0xffffffff
        t = n-4096
        v = 0 if t < 0 or t >= 32000 else (seed/4294967296-.5)*.5*math.exp(-(t%8000)/350)
        values.append(round(v*8388608))
    stereo = [v for value in values for v in (value, value)]
    if args.input_stereo:
        data = array.array('i')
        data.frombytes(args.input_stereo.read_bytes())
        if sys.byteorder != 'little':
            data.byteswap()
        if not data or len(data) % 32 or any(v < -8388608 or v > 8388607 for v in data):
            ap.error('--input-stereo requires signed 24-bit stereo in whole 16-frame blocks')
        values = stereo = data
        count = len(stereo) // 2
    def raw(path, samples):
        data=array.array('i',samples)
        if sys.byteorder != 'little':data.byteswap()
        path.write_bytes(data.tobytes())
    raw(out/'input.raw',values)
    params=controls+[127]+[0]*6
    base=[str(args.host),'-mem',str(out/'A.mem'),'-memB',str(out/'B.mem'),
          '-init',format(symbols['init'],'x'),'-proc',format(symbols['proc'],'x'),
          '-inst','2','-core','0,1','-alloc','1,1','-r7','2,2','-audioidx','0,0',
          '-frames','16','-blocks',str(count//16),'-in',str(out/'input.raw')+','+str(out/'input.raw'),
          '-split',str(args.split),
          '-allocproc','end','-audio','0','-guard',str(buffer_words),'-guard-shared','-dirty','1776']
    if args.input_stereo:
        base.append('-stereo')
    reports={}
    for name,mix in [('wet',127),('dry',0)]:
        p=params.copy();p[5]=mix
        cmd=base+['-params',','.join(map(str,p)),'-params',','.join(map(str,p)),
                  '-out',str(out/(name+'.raw')),'-meter',str(out/(name+'.meter'))]
        run=subprocess.run(cmd,capture_output=True,text=True,timeout=300)
        (out/(name+'.log')).write_text(run.stdout+run.stderr)
        if run.returncode:raise RuntimeError((run.stdout+run.stderr)[-2000:])
        channels=[]
        for suffix in ('','.i1'):
            data=array.array('i');data.frombytes(Path(str(out/(name+'.raw'))+suffix).read_bytes())
            if sys.byteorder!='little':data.byteswap()
            if len(data)!=count*2:raise RuntimeError('Truncated render')
            channels.append(data)
        if channels[0]!=channels[1]:raise RuntimeError('Core outputs differ')
        if name=='dry' and list(channels[0]) != list(stereo):
            raise RuntimeError('Dry bypass is not exact')
        if name=='wet' and not any(channels[0][8192:]):raise RuntimeError('Wet core is silent')
        with wave.open(str(out/(name+'.wav')),'wb') as wav:
            wav.setnchannels(2);wav.setsampwidth(3);wav.setframerate(32000)
            wav.writeframes(b''.join((v&0xffffff).to_bytes(3,'little') for v in channels[0]))
        meters=[[int(v) for v in row.split()] for row in (out/(name+'.meter')).read_text().splitlines()]
        reports[name]={'peakInstructionsPer16Frames':[max(row[k] for row in meters) for k in (1,2)],
                       'peakSample':max(abs(v) for v in channels[0]),'coreOutputsIdentical':True}
    # Compile the unchanged-source floating point oracle, then align the 102
    # bounded clearing calls which the experiment passes through unprocessed.
    oracle=[os.environ.get('CXX','c++'),'-std=c++17','-O2','-DTEST','-ffp-contract=off',
            '-I'+str(ROOT/'upstream'),str(ROOT/'oracle_render.cpp'),'-o',str(out/'oracle')]
    if sys.platform=='darwin':
        sdk=subprocess.check_output(['xcrun','--show-sdk-path'],text=True).strip()
        oracle[1:1]=['-isystem',sdk+'/usr/include/c++/v1']
    subprocess.run(oracle,check=True)
    skip=102*16 if args.split == 0 else 51*16
    (out/'oracle-input.f32').write_bytes(b''.join(struct.pack('<f',v/8388608) for v in stereo[skip*2:]))
    time,damp,diff,smear,gain=controls
    coefficients=[.98*time/127,.95*diff/127,.9-.85*damp/127,table[gain]/8388608,
                  1,1 if smear == 127 else smear/128]
    subprocess.run([str(out/'oracle'),str(out/'oracle-input.f32'),str(out/'oracle-output.f32'),
                    *map(str,coefficients)],check=True)
    reference=array.array('f');reference.frombytes((out/'oracle-output.f32').read_bytes())
    actual=array.array('i');actual.frombytes((out/'wet.raw').read_bytes())
    if sys.byteorder!='little':reference.byteswap();actual.byteswap()
    actual=actual[skip*2:]
    error=sum((a/8388608-b)**2 for a,b in zip(actual,reference))
    energy=sum(b*b for b in reference)
    reports['referenceErrorDb']=10*math.log10(error/max(energy,1e-30)) if error else -300
    reports['scope']='32 kHz experimental core only; no SRC, smoothing, instrument image or release qualification'
    reports['params']=params
    reports['bufferWords']=buffer_words
    reports['inputStereo']=bool(args.input_stereo)
    reports['split']=args.split
    reports['oracleCoefficients']=coefficients
    reports['sourceHashes']={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
                            for name in ('core32.asm','generate_core.py','oracle_render.cpp','packed_probe.asm')}
    reports['sourceSha256']=hashlib.sha256((ROOT/'core32.asm').read_bytes()).hexdigest()
    if args.compare_output:
        before=json.loads((args.compare_output/'core-report.json').read_text())
        if before['params'] != params or before.get('split',0) != args.split:
            raise RuntimeError('Baseline settings differ')
        for name in ('input.raw','wet.raw','wet.raw.i1','dry.raw','dry.raw.i1'):
            if (out/name).read_bytes() != (args.compare_output/name).read_bytes():
                raise RuntimeError('Optimization changed '+name)
        reports['baselineComparison']={
            'sourceSha256':before['sourceSha256'],
            'bothCoreWetAndDryBitExact':True,
            'baselinePeakInstructionsPer16Frames':before['wet']['peakInstructionsPer16Frames'],
        }
    (out/'core-report.json').write_text(json.dumps(reports,indent=2)+'\n')
    print(json.dumps(reports,indent=2))


if __name__=='__main__':main()
