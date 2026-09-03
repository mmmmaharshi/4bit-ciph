"""
QUARTET — PDH-based hardware counter TVLA (Level 2 software).

Extends the software TVLA counter set with PDH-accessible hardware
counters. These are still software-observable (not hardware traces),
but provide more signal than psutil alone.

Available via PDH (no admin required):
  - Processor time, interrupt time, DPC rate
  - C-state transitions (C1/C2/C3) - power state changes
  - DPCs queued, interrupts/sec

NOT available without admin/kernel driver:
  - L1/L2/L3 cache miss counters
  - Branch misprediction counters
  - TLB miss counters
  - Actual PMU hardware counters

For true Level 2 TVLA (power/EM traces), hardware measurement equipment
is required. This module provides the best software-only approximation.

Mano H. | 2026
"""
from __future__ import annotations

import time
from typing import Optional

try:
    import win32pdh
    HAS_WIN32PDH = True
except ImportError:
    HAS_WIN32PDH = False

# PDH counter paths (Windows Performance Data Helper)
# These are the hardware-level counters accessible without admin
PDH_COUNTERS = [
    ("Processor Time",       r"\Processor(_Total)\% Processor Time"),
    ("Interrupt Time",       r"\Processor(_Total)\% Interrupt Time"),
    ("DPC Time",             r"\Processor(_Total)\% DPC Time"),
    ("Idle Time",            r"\Processor(_Total)\% Idle Time"),
    ("C1 Transitions",       r"\Processor(_Total)\C1 Transitions/sec"),
    ("C2 Transitions",       r"\Processor(_Total)\C2 Transitions/sec"),
    ("C3 Transitions",       r"\Processor(_Total)\C3 Transitions/sec"),
    ("DPCs Queued",          r"\Processor(_Total)\DPCs Queued/sec"),
    ("Interrupts/sec",       r"\Processor(_Total)\Interrupts/sec"),
    # Memory counters
    ("Cache Faults/sec",     r"\Memory\Cache Faults/sec"),
    ("Page Faults/sec",      r"\Memory\Page Faults/sec"),
]

# Counters that are known to be UNAVAILABLE without admin/ETW
UNAVAILABLE_COUNTERS = [
    "L1 Cache Misses",
    "L2 Cache Misses",
    "L3 Cache Misses",
    "Branch Mispredictions",
    "TLB Misses",
    "Instructions Retired",
    "Cycles",
]


class PDHCounterSession:
    """PDH-based hardware counter snapshot session."""

    def __init__(self) -> None:
        if not HAS_WIN32PDH:
            raise RuntimeError("win32pdh not available (install pywin32)")
        self.query = None
        self.counters: dict[str, tuple[str, object]] = {}  # name -> (path, handle)
        self._open()

    def _open(self) -> None:
        """Open PDH query and add counters."""
        self.query = win32pdh.OpenQuery()
        for name, path in PDH_COUNTERS:
            try:
                handle = win32pdh.AddCounter(self.query, path)
                self.counters[name] = (path, handle)
            except Exception:
                # Counter not available on this system
                pass

    def snapshot(self) -> dict[str, float]:
        """Take a snapshot of all available counters."""
        if not self.query:
            return {}
        win32pdh.CollectQueryData(self.query)
        result = {}
        for name, (path, handle) in self.counters.items():
            try:
                _, value = win32pdh.GetFormattedCounterValue(handle, win32pdh.PDH_FMT_DOUBLE)
                result[name] = value
            except Exception:
                result[name] = 0.0
        return result

    def close(self) -> None:
        """Close the PDH query."""
        if self.query:
            win32pdh.CloseQuery(self.query)
            self.query = None

    def __enter__(self) -> "PDHCounterSession":
        return self

    def __exit__(self, *args) -> None:
        self.close()


def get_available_counters() -> list[str]:
    """Return list of available counter names on this system."""
    if not HAS_WIN32PDH:
        return []
    try:
        with PDHCounterSession() as session:
            snapshot = session.snapshot()
            return list(snapshot.keys())
    except Exception:
        return []


def test_pdh_available() -> bool:
    """Test if PDH is available and working."""
    if not HAS_WIN32PDH:
        return False
    try:
        with PDHCounterSession() as session:
            snapshot = session.snapshot()
            return len(snapshot) > 0
    except Exception:
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("PDH Hardware Counter TVLA Test")
    print("=" * 60)

    if not HAS_WIN32PDH:
        print("FAIL: win32pdh not available")
        print("Install: pip install pywin32")
        exit(1)

    print(f"\nPDH available: {test_pdh_available()}")

    with PDHCounterSession() as session:
        print("\nTaking snapshots (3 samples, 0.5s apart)...")
        for i in range(3):
            snap = session.snapshot()
            print(f"\nSample {i+1}:")
            for name, value in sorted(snap.items()):
                print(f"  {name}: {value:.2f}")
            if i < 2:
                time.sleep(0.5)

    print("\n" + "=" * 60)
    print("Available counters:", len(get_available_counters()))
    print("=" * 60)
