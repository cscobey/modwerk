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
            def run(directory,mode,*args):subprocess.run([str(program),str(directory),mode,*map(str,args)],check=True,capture_output=True)
            directory,old=fixture('normal')
            run(directory,'init');run(directory,'restart')
            for slot in range(2):self.assertEqual((directory/f'A/MIDI3_{slot}.DAT').read_bytes(),old)
            for cut in range(1,7):
                directory,_=fixture(f'cut-{cut}')
                run(directory,'init',cut)
                run(directory,'recover-old' if cut<4 else 'recover-new')
            directory,_=fixture('write-failure');run(directory,'failed-save')
            directory,_=fixture('protected-copy');run(directory,'protected-copy')
            directory,_=fixture('foreign')
            foreign=directory/'A/MIDI4_J0.DAT';foreign.write_bytes(b'foreign'.ljust(4096,b'\0'))
            run(directory,'foreign');self.assertEqual(foreign.read_bytes(),b'foreign'.ljust(4096,b'\0'))


if __name__=='__main__':unittest.main()
