#!/usr/bin/env python3
"""Native profile/card restart test. All inputs are panel events; outputs stay private."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import selectors
import subprocess
import struct
import time
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['emulator', 'candidate', 'receipt', 'output', 'stock']:
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--origin', type=lambda n:int(n,0), required=True)
    a = p.parse_args()
    out = a.output.resolve()
    if any((v/'.git').exists() for v in [out,*out.parents]):
        p.error('private outputs must be outside Git')
    out.mkdir(parents=True,exist_ok=False)
    spec=importlib.util.spec_from_file_location('card_tools',ROOT/'sdk/octabam/tools/emu/emu_card.py')
    card=importlib.util.module_from_spec(spec);spec.loader.exec_module(card)
    tree=out/'tree';(tree/'TEST/PROFILE').mkdir(parents=True)
    (tree/'TEST/AUDIO').mkdir()
    image=out/'card.private.img';image.write_bytes(card.build_image(tree,size_mb=32))
    symbols=json.loads(a.receipt.read_text())['symbols']
    # The stock reconstruction has no runtime registry. An authored, private
    # UI-tick shim supplies only the base's ordinary hook-0 scheduling; file
    # routines, engine service and name/channel edits still execute unchanged.
    stub_at=0x400d7c00
    stub_source=out/'tick.private.s'
    stub_source.write_text('''.text
jsr 0x4005213c
jsr 0x4007e940
lea %sp@(-16),%sp
moveml %d0-%d1/%a0-%a1,%sp@
clrl %sp@-
jsr '''+hex(a.origin+symbols['mm_profile_tick'])+'''
addql #4,%sp
moveml %sp@,%d0-%d1/%a0-%a1
lea %sp@(16),%sp
jmp 0x40052228
''')
    subprocess.run(['m68k-elf-as','-mcpu=54455','-o',str(out/'tick.o'),str(stub_source)],check=True)
    subprocess.run(['m68k-elf-ld','-Ttext',hex(stub_at),'-o',str(out/'tick.elf'),str(out/'tick.o')],check=True,capture_output=True)
    subprocess.run(['m68k-elf-objcopy','-O','binary',str(out/'tick.elf'),str(out/'tick.private.bin')],check=True)
    original=a.candidate.read_bytes();native=bytearray(original);stub=(out/'tick.private.bin').read_bytes()
    stock=a.stock.read_bytes()
    assert hashlib.sha256(stock).hexdigest()=='164f31224bf61181e3f50e7dec40df9afcae5b16dbf6e4c0d0cc5e986af0a84e'
    expect_empty=native[stub_at-0x40000400:stub_at-0x40000400+len(stub)]
    assert not any(expect_empty) and a.origin+json.loads(a.receipt.read_text())['imageBytes']<=stub_at
    native[stub_at-0x40000400:stub_at-0x40000400+len(stub)]=stub
    native[0x4005221e-0x40000400:0x40052228-0x40000400]=struct.pack('>HIHH',0x4ef9,stub_at,0x4e71,0x4e71)
    candidate=out/'scheduled.private.bin';candidate.write_bytes(native)
    checks=[]
    def expect(condition,message):
        if not condition:raise AssertionError(message)
        checks.append(message)
    for phase in ['create','restart']:
        log=(out/(phase+'.private.log')).open('w')
        port=subprocess.Popen([str(a.emulator.resolve()),'--image',str(candidate),'--mkii',
            '--boot-logo','--ms','4000','--interactive','--internal-clock','--rtc','off','--main-level','off',
            '--card',str(image),'--card-rw','--mount','--set','TEST','--project','PROFILE',
            '--lcd',str(out/(phase+'.lcd.private.bin'))],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
            stderr=(out/(phase+'.stderr.private.log')).open('wb'))
        selector=selectors.DefaultSelector();selector.register(port.stdout,selectors.EVENT_READ)
        pending=b'';rows=[0]*8
        def response(prefix):
            nonlocal pending
            deadline=time.monotonic()+180
            while time.monotonic()<deadline:
                while b'\n' in pending:
                    line,pending=pending.split(b'\n',1)
                    log.write(line.decode(errors='replace')+'\n');log.flush()
                    if line.startswith(prefix):return line.decode()
                if port.poll() is not None:raise RuntimeError('emulator exited')
                if selector.select(1):pending+=os.read(port.stdout.fileno(),65536)
            raise TimeoutError('emulator reply timeout')
        def cmd(value):
            log.write('> '+value+'\n');port.stdin.write((value+'\n').encode());port.stdin.flush()
            result=response((b'ok',b'peek ',b'card ',b'err'))
            if result.startswith('err') or ('stop=' in result and 'stop=time' not in result):raise RuntimeError(result)
            return result
        def run(ms=100):cmd('run '+str(ms))
        def read(at,n):return bytes.fromhex(cmd(f'peek {hex(at)} {n}').split()[1])
        def key(code,down):
            row,bit=code>>3,1<<(code&7);rows[row]=rows[row]|bit if down else rows[row]&~bit
            cmd(f'key {32|row} {rows[row]}');run(50)
        def press(code):key(code,True);key(code,False)
        def setup():
            press(0x22);run(500);press(0x22);press(0x22);run(100)
        def channel(want):
            for _ in range(40):
                now=int.from_bytes(read(0x460d5cb4,4),'big')
                if now==want:break
                cmd(f'knob 48 {4 if now<want else -4}');run(100)
            else:raise AssertionError('channel knob did not reach target')
            press(0x31);run(1500)
        def bank(index):
            press(0x32);key(0x2f,True);press(index);key(0x2f,False);press(0);run(1500)
            expect(read(0x100b14ce,1)==bytes([index]),f'{phase}: panel selects bank {index+1}')
        def stored(index):return read(a.origin+symbols['names_store']+index*16,16).split(b'\0',1)[0]
        def profile_channels():return read(a.origin+symbols['state']+8,512)
        try:
            response(b'ready ');press(0x32);press(0x31);run(500);press(0x35);press(0x22);run(1500)
            expect(read(a.origin+symbols['loaded'],4)==b'\0\0\0\1',phase+': engine loads project profile')
            if phase=='create':
                setup();press(0x3d)
                expect(any(read(0x460e7612,4)),'native F opens stock editor')
                press(0x33);expect(read(0x460e743c,1)==b'0','native UP enters name 0')
                press(0x31);run(1500);expect(stored(0)==b'0','native YES commits project name')
                setup();channel(2);expect(profile_channels()[0]==2,'Bank 1 supplies channel 2 default')
                bank(1);expect(profile_channels()[32]==2,'Bank 2 inherits Bank 1 channel')
                setup();channel(5);expect(profile_channels()[32]==5,'Bank 2 accepts channel 5 override')
                bank(2);expect(profile_channels()[64]==2,'Bank 3 inherits Bank 1 rather than Bank 2 override')
                expect(stored(0)==b'0','same name follows bank changes')
            else:
                expect(stored(0)==b'0','fresh native process restores name from card')
                expect(profile_channels()[0]==2,'fresh native process restores Bank 1 default')
                bank(1);expect(profile_channels()[32]==5,'fresh native process restores Bank 2 override')
                setup();expect(int.from_bytes(read(0x460d5cb4,4),'big')==5,'stock SRC setup reads restored channel 5')
                bank(2);expect(profile_channels()[64]==2,'fresh native process preserves Bank 3 default')
            expect('errors=0' in cmd('card flush'),phase+': card writes flushed without errors')
            # Restore all package sites, retire its image and the private tick
            # shim while the stock editor is open. Its destination and callback
            # must remain safe for either close path after complete removal.
            setup();press(0x3d)
            expect(any(read(0x460e7612,4)),phase+': retirement starts with editor open')
            skip_lo=a.origin-0x40000400;skip_hi=skip_lo+json.loads(a.receipt.read_text())['imageBytes']
            i=0
            while i<len(stock):
                if skip_lo<=i<skip_hi:i=skip_hi;continue
                if stock[i]==original[i]:i+=1;continue
                start=i
                while i<len(stock) and stock[i]!=original[i] and not skip_lo<=i<skip_hi:i+=1
                cmd(f'poke {hex(0x40000400+start)} {stock[start:i].hex()}')
            cmd('poke 0x4005221e '+stock[0x4005221e-0x40000400:0x40052228-0x40000400].hex())
            for at in range(skip_lo,skip_hi,512):
                n=min(512,skip_hi-at);cmd(f'poke {hex(0x40000400+at)} '+('4afc'*(n//2)))
            cmd(f'poke {hex(stub_at)} '+('4afc'*(len(stub)//2)))
            press(0x31 if phase=='create' else 0x32);run(500)
            expect(not any(read(0x460e7612,4)),phase+': editor closes after module poisoning')
            setup();press(0x3d)
            expect(not any(read(0x460e7612,4)),phase+': SRC caches remain on stock after retirement')
            cmd('quit');port.wait(timeout=10)
        finally:
            if port.poll() is None:port.kill();port.wait()
            selector.close();log.close()
        files=card.extract_image(image.read_bytes())
        records=[v for k,v in files.items() if k.startswith('TEST/PROFILE/MIDI2_')]
        expect(len(records)==2,phase+': both project-local checkpoints exist')
        for record in records:
            expect(len(record)==1024 and int.from_bytes(record[-4:],'big')==zlib.crc32(record[:-4]),phase+': checkpoint checksum matches card contents')
    report={'candidateSha256':hashlib.sha256(a.candidate.read_bytes()).hexdigest(),
        'scheduledCandidateSha256':hashlib.sha256(native).hexdigest(),
        'uiTickShim':{'site':'0x4005221e','stub':hex(stub_at),'sha256':hashlib.sha256(stub).hexdigest()},
        'packageSha256':json.loads(a.receipt.read_text())['packageSha256'],'origin':hex(a.origin),
        'checks':checks,'hardware':'not tested','fixture':'Empty FAT16 card; stock firmware initializes missing working banks. No name/channel/project-file injection; explicit retirement-site restoration and code poisoning.'}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'{len(checks)} native profile/card checks passed across two fresh processes.')


if __name__=='__main__':main()
