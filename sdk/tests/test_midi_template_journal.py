"""One-time native channel setup: fault cuts at the actual C transaction edges."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import zlib

DRAFT=Path(__file__).resolve().parents[1]/'drafts/midi-cc-slots'


class TemplateJournalTests(unittest.TestCase):
    def test_initialization_migration_copy_and_power_cut_recovery(self):
        if not shutil.which('cc'):self.skipTest('Host compiler unavailable')
        with tempfile.TemporaryDirectory(prefix='midi-journal-') as folder:
            root=Path(folder);program=root/'test'
            subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror',str(DRAFT/'template/profile.c'),str(DRAFT/'template/test_profile.c'),'-o',str(program)],check=True)
            def fixture(name):
                directory=root/name
                native=bytearray(1024);native[:8]=bytes(range(1,9));native[64]=5;native[128]=12
                for project in ['A','COPY','OTHER']:
                    p=directory/project;p.mkdir(parents=True);(p/'channels.bin').write_bytes(native)
                profile=bytearray(4096);profile[:8]=b'MM2P\0\0\0\2';profile[8:12]=(7).to_bytes(4,'big')
                profile[16:20]=b'BASS';profile[152:160]=bytes(range(1,9));profile[184:192]=bytes([5,0,3,4,5,6,7,8]);profile[664]=17
                profile[673]=1;profile[688:692]=b'LEAD';profile[-4:]=zlib.crc32(profile[:-4]).to_bytes(4,'big')
                for slot in range(2):(directory/f'A/MIDI3_{slot}.DAT').write_bytes(profile)
                return directory,bytes(profile)
            def run(directory,mode,*args):
                result=subprocess.run([str(program),str(directory),mode,*map(str,args)],capture_output=True,text=True)
                self.assertEqual(result.returncode,0,mode+': '+result.stderr)
            directory,old=fixture('normal')
            run(directory,'init');run(directory,'restart')
            for slot in range(2):self.assertEqual((directory/f'A/MIDI3_{slot}.DAT').read_bytes(),old)
            for cut in range(1,7):
                directory,_=fixture(f'cut-{cut}')
                run(directory,'init',cut)
                if cut==2:
                    journals=list((directory/'A').glob('MIDI4_J*.DAT'));self.assertEqual(len(journals),2)
                    for p in journals:
                        data=p.read_bytes();self.assertEqual(data[4:8],b'\0\0\0\2');self.assertEqual(data[32:36],b'MAP2')
                run(directory,'recover-old' if cut<4 else 'recover-new')
            for tag in [b'MAP1',bytes(4)]:
                directory,_=fixture('legacy-'+tag.hex());run(directory,'init',2)
                for p in (directory/'A').glob('MIDI4_J*.DAT'):
                    data=bytearray(p.read_bytes());data[4:8]=b'\0\0\0\1';data[32:36]=tag;data[1216:3264]=bytes(2048)
                    data[-4:]=zlib.crc32(data[:-4]).to_bytes(4,'big');p.write_bytes(data)
                run(directory,'recover-old')
            directory,_=fixture('replace');run(directory,'init');run(directory,'replace');run(directory,'replace-recover-new')
            directory,_=fixture('replace-cancel');run(directory,'init');run(directory,'replace-cancel');run(directory,'replace-recover-old')
            for cut in range(1,7):
                directory,_=fixture(f'replace-cut-{cut}');run(directory,'init');run(directory,'replace',cut)
                run(directory,'replace-recover-old' if cut<4 else 'replace-recover-new')
            directory,_=fixture('write-failure');run(directory,'failed-save')
            for mode in ['cancel-before-write','cancel-after-bank']:
                directory,_=fixture(mode);run(directory,mode)
            directory,_=fixture('protected-copy');run(directory,'protected-copy')
            directory,_=fixture('foreign')
            foreign=directory/'A/MIDI4_J0.DAT';foreign.write_bytes(b'foreign'.ljust(4096,b'\0'))
            run(directory,'foreign');self.assertEqual(foreign.read_bytes(),b'foreign'.ljust(4096,b'\0'))


if __name__=='__main__':unittest.main()
