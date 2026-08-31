"""
QUARTET — counter set for software TVLA.

On Windows 11, the Performance Data Helper (PDH) registry exposes
only the Hyper-V virtual-device counter; the ``\\Processor(_Total)\\``
counter family is not registered as PDH counters on this build
(those counters are exposed via ETW / the ``Microsoft-Windows-Kernel-
Processor`` provider, which is not accessible without pywin32 or a
similar ETW binding).

The realistic counter set available without additional packages is:

  - psutil.cpu_stats() — process-level cumulative counters exposed by
    the OS: context switches, interrupts, soft_interrupts, syscalls.
    These are per-process on Linux and per-CPU on Windows; the
    deltas during a single cipher invocation are small (0-1 events)
    for fast ciphers, so we run a batch of N encryptions per trace
    to amplify the signal.
  - time.perf_counter_ns — high-resolution wall-clock timer.
    Per-trace delta is the time spent in the N encryptions.

This is a *Level 1 software t-test* in the Goodwill 2011 sense: it
measures observable system-level counters and applies the same
Welch t-test, with the same 4.5 threshold and the same Holm-Bonferroni
correction. It does NOT measure PMU counters (branch mispredictions,
cache misses, etc.); for that, ETW or hardware trace capture is
required.

The counter set is deliberately small (~5) but the methodology is
the full Schneider-Moradi 2015: t-test per counter, max |t| reported,
negative control verifies the test catches known leakage.
"""
from __future__ import annotations

import time

import psutil

# Counter catalog. Each entry is (display_name, dict_key). The
# dict_key is the key in the snapshot()/delta() dicts; the
# display_name is used only for reporting.
COUNTERS: list[tuple[str, str]] = [
    ("Context Switches", "ctx_switches"),
    ("Interrupts",       "interrupts"),
    ("Soft Interrupts",  "soft_interrupts"),
    ("Syscalls",         "syscalls"),
    ("Wall Clock (ns)",  "wall_clock_ns"),
]


def snapshot() -> dict[str, int]:
    """Return a snapshot of all counters (cumulative values).

    The psutil counters are cumulative since process start (or
    since the last reset); wall_clock is a single reading.
    """
    s = psutil.cpu_stats()
    return {
        "ctx_switches":   s.ctx_switches,
        "interrupts":     s.interrupts,
        "soft_interrupts": s.soft_interrupts,
        "syscalls":       s.syscalls,
        "wall_clock_ns":  time.perf_counter_ns(),
    }


def delta(after: dict[str, int], before: dict[str, int]) -> dict[str, int]:
    """Per-counter delta between two snapshots. Negative deltas
    (counter wrap) are clamped to 0; in practice these counters
    don't wrap during a single trace collection (1M traces << 2^32).
    """
    return {
        name: max(0, after.get(name, 0) - before.get(name, 0))
        for name in before
    }
