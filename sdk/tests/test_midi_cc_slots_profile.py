"""Persistent profile core: actual C implementation, files survive fresh processes."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

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
            for mode in ['create', 'restart', 'fallback', 'pending', 'shorten', 'shortened', 'torn', 'recovered']:
                subprocess.run([str(executable), str(root), mode], check=True, capture_output=True)
            foreign = root/'foreign'
            (foreign/'A').mkdir(parents=True)
            path = foreign/'A/MIDI2_0.DAT'
            contents = b'foreign owner'.ljust(1024, b'\0')
            path.write_bytes(contents)
            subprocess.run([str(executable), str(foreign), 'foreign'], check=True, capture_output=True)
            self.assertEqual(path.read_bytes(), contents)
