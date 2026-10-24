"""Mist Verb: unpublished Clouds reverb insert. A standalone native 44.1 kHz path exists; installation remains pending.

Keep in sdk/drafts until the complete native engine and lifecycle are verified.
The paths below are the intended module paths after promotion, not a build.
"""
from remix.schema import (BusRole, Category, Claims, DspSection, Formatter, Gate,
                          Harness, Kind, MenuEntry, Module, Param, Proof, YBase)
MODULE = Module(
    name="mist-verb", key="MIST VERB", kind=Kind.DSP_EFFECT,
    category=Category.TRACK, author="cscobey", author_url="https://github.com/cscobey",
    proof=Proof.UNTESTED,
    proof_note="Standalone native 44.1 kHz path tested; no installed effect or hardware qualification.",
    doc="Unpublished Clouds stereo reverb insert, targeting its original 32 kHz tank.",
    menu=MenuEntry(fx2_id=0x07, donor_desc=0x400d58b8,
                   abbr=b"MIST", fullname=b"Mist Verb", build_tag=False),
    params=(
        Param(b'TIME', 96, active=True, formatter=Formatter.PLAIN,
              doc='Reverb decay; feedback remains below unity.'),
        Param(b'DAMP', 64, active=True, formatter=Formatter.PLAIN,
              doc='Darkens the recirculating tail.'),
        Param(b'DIFF', 94, active=True, formatter=Formatter.PLAIN,
              doc='Tank all-pass diffusion; about 70 percent by default.'),
        Param(b"", 0, active=False),  # D reserved; separate diffuser removed.
        Param(b'GAIN', 83, active=True, formatter=Formatter.PLAIN,
              doc='Tank input gain, planned -40 to 0 dB range; about -14 dB by default.'),
        Param(b'MIX', 40, active=True, formatter=Formatter.PLAIN,
              doc='Dry/wet blend; settles to exact dry at 0 and fully wet at 127.'),
        *(Param(b"", 0, active=False) for _ in range(6)),
    ),
    dsp=DspSection(asm="modules/mist-verb/engine.asm", priority=17,
                   bus_role=BusRole.NONE, ybase=YBase.NEVER,
                   r7_latch_slot=None, gate_label=None),
    claims=Claims(stock_instance_buffer=True, buffer_words=15728),
    harness=Harness(layout_char=None, is_server=False),
    gates=(Gate("modules/mist-verb/verify.py", remix_arg=False),),
    dear={"TIME":127,"DAMP":0,"DIFF":127,"GAIN":127,"MIX":127},
)
