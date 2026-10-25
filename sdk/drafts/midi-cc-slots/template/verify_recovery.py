#!/usr/bin/env python3
"""Interrupt actual INIT after bank writes begin, then recover in a fresh VM."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from bench import Bench,card_tools


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['emulator','stock','build','saved-tree','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if out.exists() or any((d/'.git').exists() for d in [out,*out.parents]):p.error('Choose a new private output directory.')
    out.mkdir(parents=True,mode=0o700);tree=out/'tree';shutil.copytree(a.saved_tree,tree)
    card=card_tools();image=out/'card.private.img';image.write_bytes(card.build_image(tree,size_mb=64))
    original={p.name:p.read_bytes() for p in (tree/'TEST/TRIAL').glob('bank*')}
    assert len(original)==32
    b=Bench(a.emulator,a.stock,a.build,image,out/'interrupt')
    try:
        b.setup();b.press(0x3b);assert any(b.read(0x460e7612,4));b.text('APPLY');b.press(0x31)
        for _ in range(1200):
            b.run(500)
            b.cmd('card flush');files=card.extract_image(image.read_bytes())
            pending=any(d[:4]==b'MM4J' and d[12:16]==b'\0\0\0\1' for n,d in files.items() if 'MIDI4_J' in n)
            committed=any(d[:4]==b'MM4P' and d[12:16]==b'\0\0\0\1' for n,d in files.items() if 'MIDI4_' in n and 'MIDI4_J' not in n)
            changed=[name for name,data in original.items() if files['TEST/TRIAL/'+name]!=data]
            if pending and changed and not committed:break
            assert not committed,'Missed the uncommitted bank-write window.'
        else:raise AssertionError('No pending initialization with partial bank writes.')
        (out/'cut.json').write_text(json.dumps({'changedBanks':changed,'pendingIntent':pending,'committedMetadata':committed},indent=2)+'\n')
        # Quit ends the VM at this instruction slice, without running a save
        # or allowing the in-flight initialization to complete.
    finally:b.close()
    b=Bench(a.emulator,a.stock,a.build,image,out/'recover')
    try:
        for _ in range(1600):
            if b.number('loaded') and not b.number('busy') and not b.number('recovery'):break
            b.run(500)
        else:raise AssertionError('Native rollback/reload did not complete.')
        assert b.read(b.origin+b.symbols['state']+2456,4)==b'\0'*4
        b.cmd('card flush');files=card.extract_image(image.read_bytes())
        assert all(files['TEST/TRIAL/'+name]==data for name,data in original.items()),'Rollback changed original native bank contents.'
        assert b.channels()[0]==3,'Native reload did not restore the captured Bank A channel.'
        b.bank(3);assert b.channels()[0]==0,'Recovery reapplied Bank A to an uninitialized bank.'
        b.run(4000);assert b.channels()[0]==0
        (out/'report.json').write_text(json.dumps({'packageSha256':hashlib.sha256((a.build/'trial.mwrm').read_bytes()).hexdigest(),'checks':['Actual encoder confirmation starts INIT','Interrupted after native bank writes and before committed metadata','Fresh VM restores every bank byte to the pre-INIT snapshot','Native project reload completes','Marker remains uninitialized','Uninitialized Bank D remains OFF and is not remapped'],'limitations':['Private publication, tick and first-sector IRQ fixtures; not full base or physical power loss.']},indent=2)+'\n')
        print(json.dumps({'report':str(out/'report.json')}))
    finally:b.close()


if __name__=='__main__':main()
