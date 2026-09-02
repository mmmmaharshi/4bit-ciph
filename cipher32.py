# Shim — real module moved to python/cipher32.py
import python.cipher32 as _src
globals().update({k: v for k, v in vars(_src).items() if not k.startswith("__")})
from python.cipher32 import quartet32_encrypt, quartet32_decrypt, quartet32_self_test
