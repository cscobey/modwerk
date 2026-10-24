#!/usr/bin/env python3
"""Build an unqualified, stock-free USB trial package for the local development app."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REPLAYS = [('dispatch', 0x4009ef60, 6), ('assignment', 0x4009f0fe, 6),
           ('sequence_pb', 0x4009fd84, 6), ('sequence_at', 0x4009fdf8, 6),
           ('setup_press', 0x4003fc44, 8), ('setup_clamp', 0x4003a88e, 6)]

NAME_REPLAYS = [('header', 0x4004c40c, 8, 'names_header'), ('names_key', 0x4004ae08, 8, 'names_open'),
                ('names_draw', 0x40036548, 8, 'names_setup_draw'), ('names_yes', 0x4007ddd0, 6, 'names_confirm')]

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--guards', type=Path, default=HERE / 'runtime-guards.json')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--profile', action='store_true', help='Build the persistent project-profile experiment')
    p.add_argument('--receipt', type=Path)
    p.add_argument('--review-image', type=Path, help='Private authored image for reviewing copy-guard offsets')
    args = p.parse_args()
    guards = json.loads(args.guards.read_text())
    spec = importlib.util.spec_from_file_location('runtime_build', ROOT / 'sdk/runtime/loader/build.py')
    builder = importlib.util.module_from_spec(spec); spec.loader.exec_module(builder)
    with tempfile.TemporaryDirectory(prefix='cc-runtime-') as folder:
        work = Path(folder)
        source = (HERE / 'slots.s').read_text()+'\n'+(HERE / ('profile_names.s' if args.profile else 'names.s')).read_text()
        for name, _, length in [*REPLAYS, *[(n,a,l) for n,a,l,_ in NAME_REPLAYS]]:
            source = source.replace(f'.incbin "{name}.private.bin"', f'replay_{name}: .space {length}')
        source = source.replace('.incbin "\\replay"', 'replay_\\name: .space 6')
        (work / 'slots.s').write_text(source)
        def run(*cmd):
            return subprocess.check_output(cmd, cwd=work, text=True)
        run('m68k-elf-as', '-mcpu=54455', '-o', 'slots.o', 'slots.s')
        units = ['slots.o']
        if args.profile:
            for file in ['profile.c', 'profile_140c.c']:
                obj = file+'.o'
                run('m68k-elf-gcc','-Os','-mcpu=54455','-msoft-float','-fno-builtin','-fno-common','-fno-late-combine-instructions','-ffreestanding','-c',str(HERE/file),'-o',obj)
                units.append(obj)
            guard_spec = importlib.util.spec_from_file_location('codegen_guard', ROOT / 'sdk/runtime/m68k_codegen.py')
            codegen = importlib.util.module_from_spec(guard_spec); guard_spec.loader.exec_module(codegen)
            codegen.check([work / unit for unit in units[1:]])
        images, symbols = [], []
        for index, origin in enumerate((0, builder.SHIFT)):
            if args.profile:
                (work/'dense.ld').write_text('SECTIONS { . = '+hex(origin)+'; .text : { *(.text*) *(.rodata*) *(.data*) *(.bss*) *(COMMON) BYTE(0) . = ALIGN(4); } }')
                run('m68k-elf-ld','-e','slot_dispatch','-T','dense.ld','-o',f'{index}.elf',*units)
            else:
                run('m68k-elf-ld', '-e', 'slot_dispatch', '-Ttext', hex(origin), '-o', f'{index}.elf', 'slots.o')
            run('m68k-elf-objcopy', '-O', 'binary', f'{index}.elf', f'{index}.bin')
            images.append((work / f'{index}.bin').read_bytes())
            symbols.append({line.split()[2]: int(line.split()[0], 16) for line in run('m68k-elf-nm', '--defined-only', f'{index}.elf').splitlines()})
        image = bytearray(images[0])
        offsets = builder.relocations(image, images[1], len(image))
        sym = symbols[0]
        if args.review_image:
            args.review_image.parent.mkdir(parents=True,exist_ok=True)
            args.review_image.write_bytes(image)
        copies = [(sym['replay_' + ('slot_' if name.startswith('sequence_') else '') + name], address, length, bytes.fromhex(guards[hex(address)])) for name, address, length in REPLAYS]
        copies += [(sym['replay_'+name], address, length, bytes.fromhex(guards[hex(address)])) for name,address,length,_ in NAME_REPLAYS]
        # Authored instruction runs that coincide with stock use the same hash-copy
        # mechanism; never ship a stock-overlap scanner exemption.
        for copy in json.loads((HERE / ('runtime-copies-profile.json' if args.profile else 'runtime-copies.json')).read_text()):
            at, n = copy['offset'], copy['length']
            if hashlib.sha256(image[at:at+n]).hexdigest() != copy['sha256']:
                raise ValueError('The reviewed authored copy changed; inspect the new source.')
            image[at:at+n] = bytes(n)
            copies.append((at, int(copy['address'], 16), n, bytes.fromhex(copy['sha256'])))
        sites = []
        def site(address, data, reloc=()):
            sites.append((address, bytes.fromhex(guards[hex(address)]), data, reloc, 0, len(data)))
        for name, address, length in REPLAYS:
            code = struct.pack('>HI', 0x4ef9, sym['slot_' + name]) + (b'\x4e\x71' if length == 8 else b'')
            site(address, code, (2,))
        descriptor = 0x400d42f4
        site(descriptor + 0x3a, b'PB\0\0\0\0AT\0\0\0\0')
        site(0x4004e474, struct.pack('>HI', 0x4ef9, sym['slot_label']), (2,))
        site(0x4003fbc4, struct.pack('>HIHH', 0x4ef9, sym['slot_setup_label'], 0x4e71, 0x4e71), (2,))
        for index in range(2):
            site(descriptor + 0xb2 + 4*index, struct.pack('>I', 129))
            site(descriptor + 0xe2 + 4*index, struct.pack('>I', sym['slot_format']), (0,))
            site(descriptor + 0x112 + 4*index, struct.pack('>I', 0x400467a4))
        site(descriptor + 0x18e, struct.pack('>I', 0x11111111))
        for _, address, length, symbol in NAME_REPLAYS:
            site(address, struct.pack('>HI', 0x4ef9, sym[symbol])+(b'\x4e\x71' if length == 8 else b''), (2,))
        if args.profile:
            site(0x40084854, struct.pack('>HI',0x4eb9,sym['names_engine']), (2,))
        builder.unevented(sites, copies)
        data = builder.package(image, 0, [sym['mm_profile_tick'] if args.profile else builder.NONE]+[builder.NONE]*3, offsets, sites, name='midi-cc-slots',
                               hashed=True, title='MIDI CC SLOTS', copies=copies)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(data)
        if args.receipt:
            args.receipt.write_text(json.dumps({'symbols':sym,'imageBytes':len(image),'profile':args.profile,'packageSha256':hashlib.sha256(data).hexdigest()},indent=2)+'\n')
        print(json.dumps({'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'relocations': len(offsets), 'sites': len(sites), 'copies': len(copies)}))

if __name__ == '__main__':
    main()
