"""Persistent profile core: actual C implementation, files survive fresh processes."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import zlib

DRAFT = Path(__file__).resolve().parents[1] / 'drafts/midi-cc-slots'


class MidiProfileTests(unittest.TestCase):
    def test_project_defaults_overrides_and_checkpoint_failures(self):
        if not shutil.which('cc'):
            self.skipTest('host C compiler unavailable')
        with tempfile.TemporaryDirectory(prefix='midi-profile-') as folder:
            root = Path(folder)
            executable = root / 'profile'
            subprocess.run(['cc', '-std=c99', '-O2', '-Wall', '-Wextra', '-Werror',
                            str(DRAFT/'profile.c'), str(DRAFT/'test_profile.c'), '-o', str(executable)], check=True)
            for project in ['A', 'B']:
                (root/project).mkdir()
            for mode in ['create', 'restart', 'fallback', 'pending', 'shorten', 'shortened', 'torn', 'recovered', 'repaired']:
                subprocess.run([str(executable), str(root), mode], check=True, capture_output=True)
            foreign = root/'foreign'
            (foreign/'A').mkdir(parents=True)
            path = foreign/'A/MIDI3_0.DAT'
            contents = b'foreign owner'.ljust(4096, b'\0')
            path.write_bytes(contents)
            subprocess.run([str(executable), str(foreign), 'foreign'], check=True, capture_output=True)
            self.assertEqual(path.read_bytes(), contents)

            migrated=root/'migration'
            (migrated/'A').mkdir(parents=True)
            legacy=bytearray(1024)
            legacy[:4]=b'MM2P'
            legacy[4:8]=(1).to_bytes(4,'big')
            legacy[8:12]=(5).to_bytes(4,'big')
            legacy[16:23]=b'LEGACY1'
            legacy[144:152]=bytes(range(1,9))
            legacy[152:160]=bytes(range(1,9))
            legacy[184:192]=bytes([12,0,3,4,5,6,7,8])
            legacy[664]=17
            legacy[-4:]=zlib.crc32(legacy[:-4]).to_bytes(4,'big')
            old=migrated/'A/MIDI2_0.DAT';old.write_bytes(legacy)
            newer=bytearray(legacy);newer[8:12]=(6).to_bytes(4,'big');newer[-4:]=zlib.crc32(newer[:-4]).to_bytes(4,'big')
            peer=migrated/'A/MIDI2_1.DAT';peer.write_bytes(newer)
            for mode in ['migration','migrated']:
                subprocess.run([str(executable),str(migrated),mode],check=True,capture_output=True)
            self.assertEqual(old.read_bytes(),bytes(legacy))
            self.assertEqual(peer.read_bytes(),bytes(newer))
            self.assertTrue((migrated/'A/MIDI3_0.DAT').exists())
