"""Local USB draft declaration; not registered with the native card composer.

The original runtime adapter is compiled by build_runtime.py. Presentation
and local catalogue metadata live in local-module.json. A public card recipe
and release qualification remain separate work.
"""

MODULE_ID = 'midi-cc-slots'
VERSION = '0.0.5-experimental'
RUNTIME_BUILDER = 'build_runtime.py'
NATIVE_CARD_SUPPORTED = False
