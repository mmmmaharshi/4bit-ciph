"""
QUARTET — Python leaky reference for TVLA negative control.

The real cipher (`cipher.py`) is constant-time by construction: no
data-dependent branches, no data-dependent memory access. The
Welch t-test on the real cipher's hardware counter deltas should
show no |t| above the 4.5 threshold.

To prove the t-test methodology is not vacuous, this module is a
deliberately-leaky variant of the cipher that branches on a key
bit. The leak is observable as a wall-clock difference: when the
top bit of the key is 1, the leaky variant sleeps for 1ms before
encrypting; when it is 0, it does not. The wall-clock delta is
~1ms per trace, vs ~30us for a normal trace (Cohen's d ~ 30,
detectable with 1 trace).

This is the negative control. A passing t-test on the real cipher
combined with a failing t-test on this leaky variant demonstrates
that the t-test methodology is sound.
"""
from __future__ import annotations

import time

from cipher import quartet_encrypt


def leaky_quartet_encrypt(plaintext: int, key: int) -> int:
    """Encrypt exactly like quartet_encrypt, but with a key-dependent
    sleep that the real cipher does not have.
    """
    if (key >> 63) & 1:
        time.sleep(0.001)  # 1 ms
    return quartet_encrypt(plaintext, key)
