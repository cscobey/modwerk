#!/usr/bin/env python3
"""Build an emulator-only MIDI name experiment from a private original MAIN.

No USB package or card firmware is produced. All outputs must stay outside Git.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess

BASE = 0x40000400
PLACEMENT = 0x400d6b20
STOCK = '164f31224bf61181e3f50e7dec40df9afcae5b16dbf6e4c0d0cc5e986af0a84e'
HERE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if any((parent/'.git').exists() for parent in [output, *output.parents]):
        parser.error('outputs must be outside every Git checkout')
    stock = args.stock.read_bytes()
    if sha(stock) != STOCK:
        parser.error('requires the verified original stock 1.40C MAIN')
    output.mkdir(parents=True, exist_ok=False)
    (output/'header.private.bin').write_bytes(stock[0x4004c40c-BASE:0x4004c414-BASE])

    def run(*args):
        return subprocess.check_output(args, cwd=output, text=True)

    run('m68k-elf-as', '-mcpu=54455', '-o', 'names.o', str(HERE/'names.s'))
    run('m68k-elf-ld', '-e', 'names_open', '-Ttext', hex(PLACEMENT), '-o', 'names.elf', 'names.o')
    run('m68k-elf-objcopy', '-O', 'binary', 'names.elf', 'names.private.bin')
    symbols = {fields[2]: int(fields[0], 16) for line in run('m68k-elf-nm', '--defined-only', 'names.elf').splitlines() if (fields := line.split())}
    code = (output/'names.private.bin').read_bytes()
    if PLACEMENT+len(code) > 0x400d7bbc or any(stock[PLACEMENT-BASE:PLACEMENT-BASE+len(code)]):
        raise ValueError('solo emulator placement is not empty')
    image = bytearray(stock)
    image[PLACEMENT-BASE:PLACEMENT-BASE+len(code)] = code
    writes = []

    def write(address, data):
        writes.append({'address': hex(address), 'bytes': len(data), 'originalSha256': sha(stock[address-BASE:address-BASE+len(data)])})
        image[address-BASE:address-BASE+len(data)] = data

    write(0x4004c40c, struct.pack('>HIH', 0x4ef9, symbols['names_header'], 0x4e71))
    # This shared handler is gated to MIDI NOTE SETUP; other contexts tail-call stock.
    write(0x400bc5d8, struct.pack('>II', symbols['names_open'], symbols['names_open']))
    write(0x400bc6e4, struct.pack('>I', symbols['names_setup_draw']))
    (output/'candidate.private.bin').write_bytes(image)
    receipt = {'stockSha256': STOCK, 'candidateSha256': sha(image), 'sourceSha256': sha((HERE/'names.s').read_bytes()),
               'builderSha256': sha(Path(__file__).read_bytes()), 'placement': hex(PLACEMENT), 'symbols': symbols, 'writes': writes,
               'qualification': 'solo emulator experiment only; volatile names; no project lifecycle or runtime composition'}
    (output/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps({'candidateSha256': receipt['candidateSha256'], 'authoredBytes': len(code)}))


if __name__ == '__main__':
    main()
