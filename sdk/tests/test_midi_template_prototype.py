"""Isolated template research; production v7 is not switched to this core."""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

PROTOTYPE=Path(__file__).resolve().parents[1]/'drafts/midi-cc-slots/prototype'


class TemplatePrototypeTests(unittest.TestCase):
    def test_name_clone_project_isolation_failure_and_no_channel_restore(self):
        if not shutil.which('cc'):self.skipTest('Host C compiler unavailable')
        with tempfile.TemporaryDirectory(prefix='midi-template-') as folder:
            root=Path(folder)
            for name in ['TEMPLATE','COPY','OTHER','COLLISION','FAIL']:(root/name).mkdir()
            foreign=root/'COLLISION/MIDI3_0.DAT';foreign.write_bytes(b'foreign'.ljust(4096,b'\0'))
            program=root/'test'
            subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror',str(PROTOTYPE/'profile.c'),str(PROTOTYPE/'test_profile.c'),'-o',str(program)],check=True)
            for mode in ['create','restart']:subprocess.run([str(program),str(root),mode],check=True)
            self.assertEqual(foreign.read_bytes(),b'foreign'.ljust(4096,b'\0'))

    def test_initializer_refuses_existing_destination_without_writing_source(self):
        spec=importlib.util.spec_from_file_location('template_stage',PROTOTYPE/'stage.py')
        stage=importlib.util.module_from_spec(spec);spec.loader.exec_module(stage)
        with tempfile.TemporaryDirectory(prefix='midi-template-stage-') as folder:
            root=Path(folder);source=root/'source';source.mkdir();dest=root/'existing';dest.mkdir()
            (source/'sentinel').write_bytes(b'unchanged')
            with self.assertRaises(ValueError):stage.stage(source,dest)
            self.assertEqual((source/'sentinel').read_bytes(),b'unchanged')
            with self.assertRaises(KeyError):stage.stage(source,root/'new')
            self.assertFalse((root/'new').exists())


if __name__=='__main__':unittest.main()
