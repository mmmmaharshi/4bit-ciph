"""Test ETW (Event Tracing for Windows) access for PMU counters."""
import sys
import subprocess


def check_etw_providers():
    """Check what ETW providers are available."""
    print("[1] Checking ETW providers...")
    try:
        result = subprocess.run(
            ["logman", "query", "providers"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            providers = result.stdout.split('\n')
            # Look for processor-related providers
            proc_providers = [p for p in providers if 'rocessor' in p or 'PMU' in p]
            print(f"Found {len(proc_providers)} processor-related providers")
            for p in proc_providers[:10]:
                print(f"  {p.strip()}")
            return proc_providers
        else:
            print(f"logman error: {result.stderr}")
            return []
    except Exception as e:
        print(f"FAIL: {e}")
        return []


def check_etw_sessions():
    """Check active ETW sessions."""
    print("\n[2] Checking active ETW sessions...")
    try:
        result = subprocess.run(
            ["logman", "query", "-ets"],
            capture_output=True, text=True, timeout=10
        )
        print(result.stdout[:500] if result.stdout else "No active sessions")
    except Exception as e:
        print(f"FAIL: {e}")


def try_pmu_counters():
    """Try to access PMU counters via typeperf."""
    print("\n[3] Checking PMU counters via typeperf...")
    # List all counters
    try:
        result = subprocess.run(
            ["typeperf", "-qx"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            # Look for cache/PMU related
            cache_lines = [l for l in lines if 'cache' in l.lower() or 'miss' in l.lower() or 'pmc' in l.lower()]
            print(f"Found {len(cache_lines)} cache/PMU counters")
            for l in cache_lines[:20]:
                print(f"  {l.strip()}")
            return cache_lines
        else:
            print(f"typeperf error: {result.stderr[:200]}")
            return []
    except Exception as e:
        print(f"FAIL: {e}")
        return []


def check_perf_uncore():
    """Check for uncore/PMU access."""
    print("\n[4] Checking for PMU/uncore access...")
    # Try to find if any PMU counters are exposed
    try:
        result = subprocess.run(
            ["typeperf", "-qx", "Memory"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            print("Memory counters:")
            for line in result.stdout.split('\n')[:10]:
                print(f"  {line.strip()}")
    except Exception as e:
        print(f"FAIL: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("ETW/PMU Counter Access Test")
    print("=" * 60)

    providers = check_etw_providers()
    check_etw_sessions()
    cache = try_pmu_counters()
    check_perf_uncore()

    print("\n" + "=" * 60)
    print("Test complete")
