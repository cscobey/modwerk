"""Local draft; standalone card candidate is separate from the USB listing.

The original runtime adapter is compiled by build_runtime.py. Presentation
and local catalogue metadata live in local-module.json. The private card builder
does not register a public or mixed-module card recipe.
"""

MODULE_ID = 'midi-cc-slots'
VERSION = '0.0.14-experimental'
USB_TRIAL_VERSION = '0.0.13-experimental'
RUNTIME_BUILDER = 'build_runtime.py'
CARD_BUILDER = 'build_card.py'
STANDALONE_CARD_SUPPORTED = True
NATIVE_CARD_SUPPORTED = False
