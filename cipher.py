# Shim — real module moved to python/cipher.py (keeps `import cipher` working)
import python.cipher as _src
from python.cipher import SBOX, INV_SBOX  # explicit for linters
globals().update({k: v for k, v in vars(_src).items() if not k.startswith("__")})
