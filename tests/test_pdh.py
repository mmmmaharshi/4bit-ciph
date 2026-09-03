"""Test PDH (Performance Data Helper) access for PMU counters."""
import sys
import time

def test_pdh_basic():
    """Test basic PDH counter access."""
    try:
        import win32pdh
    except ImportError:
        print("FAIL: win32pdh not available (install pywin32)")
        return False

    # Test a simple counter
    counter_path = r'\Processor(_Total)\% Processor Time'
    try:
        hq = win32pdh.OpenQuery()
        hcounter = win32pdh.AddCounter(hq, counter_path)
        win32pdh.CollectQueryData(hq)
        time.sleep(0.1)
        win32pdh.CollectQueryData(hq)
        _, value = win32pdh.GetFormattedCounterValue(hcounter, win32pdh.PDH_FMT_LONG)
        win32pdh.CloseQuery(hq)
        print(f"OK: Processor time = {value}%")
        return True
    except Exception as e:
        print(f"FAIL: PDH counter error: {e}")
        return False


def test_pdh_enumerate():
    """Enumerate available processor counters."""
    try:
        import win32pdh
    except ImportError:
        print("FAIL: win32pdh not available")
        return []

    try:
        counters, instances = win32pdh.EnumObjectItems(None, None, 'Processor', -1, 0)
        print(f"Processor instances: {instances}")
        print(f"Available counters ({len(counters)}):")
        for c in sorted(counters):
            print(f"  {c}")
        return counters
    except Exception as e:
        print(f"FAIL: Enumeration error: {e}")
        return []


def test_cache_counters():
    """Check for cache-related counters."""
    try:
        import win32pdh
    except ImportError:
        return []

    # Look for cache-related counters
    cache_paths = [
        r'\Processor(_Total)\Cache Misses',
        r'\Processor(_Total)\L2 Cache Misses',
        r'\Memory\Cache Faults/sec',
        r'\Memory\Page Faults/sec',
    ]

    found = []
    for path in cache_paths:
        try:
            hq = win32pdh.OpenQuery()
            hcounter = win32pdh.AddCounter(hq, path)
            win32pdh.CollectQueryData(hq)
            _, value = win32pdh.GetFormattedCounterValue(hcounter, win32pdh.PDH_FMT_LONG)
            win32pdh.CloseQuery(hq)
            print(f"OK: {path} = {value}")
            found.append(path)
        except Exception as e:
            print(f"MISSING: {path}")

    return found


if __name__ == "__main__":
    print("=" * 60)
    print("PDH/PMU Counter Access Test")
    print("=" * 60)

    print("\n[1] Basic PDH access:")
    ok = test_pdh_basic()

    if ok:
        print("\n[2] Enumerating processor counters:")
        counters = test_pdh_enumerate()

        print("\n[3] Cache/memory counters:")
        cache = test_cache_counters()

    print("\n" + "=" * 60)
    print("Test complete")
