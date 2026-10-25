"""Preserve complete bank contents around checked channel-sector updates."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

DRAFT=Path(__file__).resolve().parents[1]/'drafts/midi-cc-slots/template'
SIZE=636113


class TemplateBankTests(unittest.TestCase):
    def test_sector_patching_repair_and_saved_project_preflight(self):
        if not shutil.which('cc'):self.skipTest('Host compiler unavailable')
        with tempfile.TemporaryDirectory(prefix='midi-banks-') as folder:
            root=Path(folder);program=root/'test'
            subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror',str(DRAFT/'banks.c'),str(DRAFT/'test_banks.c'),'-o',str(program)],check=True)
            originals={}
            for bank in range(16):
                data=bytearray(bytes((i*37+bank)%256 for i in range(256))*(SIZE//256+1))[:SIZE]
                data[:4]=b'FORM';data[8:16]=b'DPS1BANK'
                for part in range(8):
                    start=0x8eed6+part*0x18bb;data[start:start+4]=b'PART'
                    for track in range(8):data[start+9+0x4e2+track*36]=(bank+part+track)%17
                data[-2:]=(sum(data[16:-2])&65535).to_bytes(2,'big')
                originals[bank]=bytes(data)
            for mode in ['apply','work','strd','checksum','both-bad','unsaved','missing','newedit']:
                case=root/mode;case.mkdir()
                for bank,data in originals.items():
                    for suffix in ['work','strd']:(case/f'bank{bank+1:02d}.{suffix}').write_bytes(data)
                if mode=='unsaved':
                    data=bytearray(originals[0]);data[42]^=0x55;data[-2:]=(sum(data[16:-2])&65535).to_bytes(2,'big');(case/'bank01.strd').write_bytes(data)
                if mode=='missing':(case/'bank16.strd').unlink()
                before={p.name:p.read_bytes() for p in case.iterdir()}
                subprocess.run([str(program),str(case),mode],check=True,capture_output=True)
                for path in case.iterdir():
                    result=path.read_bytes();self.assertEqual(len(result),SIZE)
                    if mode=='apply':
                        expected=bytearray(before[path.name])
                        for part in range(8):
                            for track in range(8):expected[0x8eed6+part*0x18bb+9+0x4e2+track*36]=track+1
                        expected[-2:]=(sum(expected[16:-2])&65535).to_bytes(2,'big')
                        self.assertEqual(result,expected)
                    elif mode!='both-bad':self.assertEqual(result,before[path.name])
                if mode=='missing':self.assertFalse((case/'bank16.strd').exists())


if __name__=='__main__':unittest.main()
