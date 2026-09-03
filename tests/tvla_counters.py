"""
QUARTET — counter set for software TVLA.

Two counter sources:

1. **psutil** (always available): process-level cumulative counters
   (context switches, interrupts, soft-interrupts, syscalls) plus
   wall-clock time. These are per-process on Linux and per-CPU on
   Windows.

2. **PDH** (Windows, requires pywin32): hardware-level performance
   counters via Performance Data Helper. Provides processor time,
   interrupt time, C-state transitions, DPCs, and memory fault
   counters. Still software-observable (not hardware traces), but
   more signal than psutil alone.

On Windows 11, the PDH path exposes more counters than psutil but
still does NOT include L1/L2/L3 cache misses, branch mispredictions,
or TLB misses. Those require ETW kernel tracing (admin) or hardware
trace capture (oscilloscope/EM probe).

For true Level 2 TVLA (power/EM traces), hardware measurement
equipment is required. This module provides the best software-only
approximation.

Mano H. | 2026
"""
from __future__ import annotations

import time

import psutil

# Try to import PDH (requires pywin32 on Windows)
try:
    import win32pdh
    HAS_WIN32PDH = True
except ImportError:
    HAS_WIN32PDH = False

# psutil-based counters (always available)
PSUTIL_COUNTERS: list[tuple[str, str]] = [
    ("Context Switches", "ctx_switches"),
    ("Interrupts",       "interrupts"),
    ("Soft Interrupts",  "soft_interrupts"),
    ("Syscalls",         "syscalls"),
    ("Wall Clock (ns)",  "wall_clock_ns"),
]

# PDH-based counters (Windows with pywin32)
# These are hardware-level but still software-observable
# Format: (display_name, key) where key is used as dict key in snapshot
PDH_COUNTERS: list[tuple[str, str]] = [
    ("PDH: Processor Time",       "pdh_processor_time"),
    ("PDH: Interrupt Time",       "pdh_interrupt_time"),
    ("PDH: DPC Time",             "pdh_dpc_time"),
    ("PDH: C1 Transitions",       "pdh_c1_transitions"),
    ("PDH: C2 Transitions",       "pdh_c2_transitions"),
    ("PDH: C3 Transitions",       "pdh_c3_transitions"),
    ("PDH: DPCs Queued",          "pdh_dpcs_queued"),
    ("PDH: Interrupts/sec",       "pdh_interrupts_sec"),
    ("PDH: Cache Faults/sec",     "pdh_cache_faults_sec"),
    ("PDH: Page Faults/sec",      "pdh_page_faults_sec"),
]

# Map PDH counter key -> PDH path for actual counter lookup
PDH_KEY_TO_PATH: dict[str, str] = {
    "pdh_processor_time":   r"\Processor(_Total)\% Processor Time",
    "pdh_interrupt_time":   r"\Processor(_Total)\% Interrupt Time",
    "pdh_dpc_time":         r"\Processor(_Total)\% DPC Time",
    "pdh_c1_transitions":   r"\Processor(_Total)\C1 Transitions/sec",
    "pdh_c2_transitions":   r"\Processor(_Total)\C2 Transitions/sec",
    "pdh_c3_transitions":   r"\Processor(_Total)\C3 Transitions/sec",
    "pdh_dpcs_queued":      r"\Processor(_Total)\DPCs Queued/sec",
    "pdh_interrupts_sec":   r"\Processor(_Total)\Interrupts/sec",
    "pdh_cache_faults_sec": r"\Memory\Cache Faults/sec",
    "pdh_page_faults_sec":  r"\Memory\Page Faults/sec",
}

# Combined counter catalog
COUNTERS: list[tuple[str, str]] = PSUTIL_COUNTERS + PDH_COUNTERS


class _PDHSession:
    """Internal PDH query session manager."""

    def __init__(self) -> None:
        self.query = None
        # Map display name -> (path, handle)
        self._counters: dict[str, tuple[str, object]] = {}
        if HAS_WIN32PDH:
            self._open()

    def _open(self) -> None:
        if not HAS_WIN32PDH:
            return
        try:
            self.query = win32pdh.OpenQuery()
            for display_name, key in PDH_COUNTERS:
                path = PDH_KEY_TO_PATH.get(key, "")
                if not path:
                    continue
                try:
                    handle = win32pdh.AddCounter(self.query, path)
                    self._counters[key] = handle
                except Exception:
                    pass  # Counter not available
        except Exception:
            self.query = None

    def snapshot(self) -> dict[str, float]:
        """Return dict mapping display name -> current value."""
        if not self.query:
            return {}
        try:
            win32pdh.CollectQueryData(self.query)
        except Exception:
            return {}
        result = {}
        for display_name, handle in self._counters.items():
            try:
                _, value = win32pdh.GetFormattedCounterValue(handle, win32pdh.PDH_FMT_DOUBLE)
                result[display_name] = value
            except Exception:
                result[display_name] = 0.0
        return result

    @property
    def handles(self) -> dict[str, tuple[str, object]]:
        """Expose counters for key mapping."""
        return {key: (PDH_KEY_TO_PATH[key], handle) for key, handle in self._counters.items() if key in PDH_KEY_TO_PATH}

    def close(self) -> None:
        if self.query and HAS_WIN32PDH:
            try:
                win32pdh.CloseQuery(self.query)
            except Exception:
                pass
            self.query = None


# Global PDH session (lazy-initialized)
_pdh_session: _PDHSession | None = None


def _get_pdh_session() -> _PDHSession:
    global _pdh_session
    if _pdh_session is None:
        _pdh_session = _PDHSession()
    return _pdh_session


def snapshot() -> dict[str, int]:
    """Return a snapshot of all counters (cumulative values).

    psutil counters are cumulative since process start.
    PDH counters are instantaneous rates.
    Wall clock is a single reading.
    """
    # psutil snapshot
    s = psutil.cpu_stats()
    result = {
        "ctx_switches":   s.ctx_switches,
        "interrupts":     s.interrupts,
        "soft_interrupts": s.soft_interrupts,
        "syscalls":       s.syscalls,
        "wall_clock_ns":  time.perf_counter_ns(),
    }

    # PDH snapshot (if available)
    if HAS_WIN32PDH:
        pdh = _get_pdh_session()
        pdh_snapshot = pdh.snapshot()
        # Convert float PDH values to int for consistency
        # Keys in pdh_snapshot are the display names from PDH_COUNTERS
        for name, value in pdh_snapshot.items():
            result[name] = int(value)

    return result


def delta(after: dict[str, int], before: dict[str, int]) -> dict[str, int]:
    """Per-counter delta between two snapshots. Negative deltas
    (counter wrap) are clamped to 0."""
    return {
        name: max(0, after.get(name, 0) - before.get(name, 0))
        for name in before
    }


def close() -> None:
    """Close the PDH session (if open)."""
    global _pdh_session
    if _pdh_session is not None:
        _pdh_session.close()
        _pdh_session = None


def has_pdh() -> bool:
    """Return True if PDH counters are available."""
    return HAS_WIN32PDH


def available_counters() -> list[str]:
    """Return list of currently available counter names."""
    return [name for name, _ in COUNTERS]


if __name__ == "__main__":
    print("TVLA Counter Set")
    print("=" * 60)
    print(f"PDH available: {has_pdh()}")
    print(f"Total counters: {len(COUNTERS)}")
    print()
    print("Counter list:")
    for name, key in COUNTERS:
        print(f"  {name}")
    print()
    print("Snapshot test:")
    snap = snapshot()
    for name, value in sorted(snap.items()):
        print(f"  {name}: {value}")
