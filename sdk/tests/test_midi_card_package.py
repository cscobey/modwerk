"""Stock-free MWRM to native format-2 translation; synthetic authored bytes only."""
import importlib.util
from pathlib import Path
import struct
import unittest

ROOT=Path(__file__).resolve().parents[2]


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


card=load('midi_card',ROOT/'sdk/drafts/midi-cc-slots/build_card.py')
runtime=load('midi_runtime_package',ROOT/'sdk/runtime/loader/build.py')


def fixture():
    image=bytearray(64);struct.pack_into('>I',image,0,8)
    sites=[(0x40002000+i*8,bytes(32),struct.pack('>HI',0x4ef9,8),(2,),0,6) for i in range(24)]
    return runtime.package(image,0,[8,runtime.NONE,16,20],[0],sites,name='midi-cc-slots',title='TEST',hashed=True,abi=8,copies=[(32,0x40004000,16,bytes(32))])


class MidiCardPackageTests(unittest.TestCase):
    def test_translates_offsets_sites_hooks_and_stock_references(self):
        doc,copies=card.card_document(fixture(),{'device':'octatrack','os':'1.40C'})
        self.assertEqual(doc['requires'],['core'])
        self.assertEqual(doc['sections']['.run']['align'],16)
        self.assertEqual(doc['relocs'],[['.run',0,'abs32','sec:.run',8]])
        self.assertEqual(doc['symbols']['midi_mode2_key'],['.run',16])
        self.assertEqual([c['to'] for c in doc['contribute']],['ev_tick','ev_key','ev_enc'])
        self.assertEqual(doc['sites'][0]['relocs'],[[2,'abs32','sec:.run',8]])
        self.assertEqual(doc['sites'][0]['new'],'4ef900000000')
        self.assertEqual(copies,[(32,0x40004000,16,'00'*32)])
        self.assertIn(['stock',0x40004000,16],doc['sections']['.run']['parts'])
    def test_refuses_truncation_wrong_identity_and_trailing_bytes(self):
        original=fixture()
        for length in [0,91,100,len(original)-1]:
            with self.subTest(length=length),self.assertRaises(ValueError):card.card_document(original[:length],{})
        for at in [0,4,7,28]:
            data=bytearray(original);data[at]^=1
            with self.subTest(at=at),self.assertRaises(ValueError):card.card_document(data,{})
        with self.assertRaises(ValueError):card.card_document(original+b'X',{})
    def test_refuses_stock_placeholder_or_local_pointer_drift(self):
        for at in [92+32,92]:
            data=bytearray(fixture());data[at]=0xff
            with self.subTest(at=at),self.assertRaises(ValueError):card.card_document(data,{})


if __name__=='__main__':unittest.main()
