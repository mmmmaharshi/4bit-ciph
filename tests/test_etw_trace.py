"""Test ETW trace session for processor/PMU events."""
import subprocess
import time
import os


def start_etw_session():
    """Start an ETW trace session for processor events."""
    print("[1] Starting ETW trace session...")
    sessionName = "QUARTET_TEST"

    # Stop any existing session
    subprocess.run(
        ["logman", "stop", sessionName, "-ets"],
        capture_output=True, text=True, timeout=10
    )

    # Start a new session with the Kernel-Processor-Power provider
    result = subprocess.run(
        [
            "logman", "start", sessionName, "-ets",
            "-p", "Microsoft-Windows-Kernel-Processor-Power",
            "0x7",  # keywords: IRQ+DPC+Cswitch+Profile
            "0x5",  # level: verbose
            "-o", ".etw_trace.etl",
            "-bs", "64",
            "-nb", "128", "256"
        ],
        capture_output=True, text=True, timeout=30
    )

    if result.returncode == 0:
        print(f"ETW session '{sessionName}' started")
        return sessionName
    else:
        print(f"FAIL: {result.stderr[:300]}")
        return None


def collect_etw_data(sessionName, duration=5):
    """Collect ETW data for specified duration."""
    print(f"\n[2] Collecting ETW data for {duration}s...")
    time.sleep(duration)

    # Query the session
    result = subprocess.run(
        ["logman", "query", sessionName, "-ets"],
        capture_output=True, text=True, timeout=10
    )
    print(result.stdout[:500] if result.stdout else "No output")
    return result.stdout


def stop_etw_session(sessionName):
    """Stop ETW trace session and convert to readable format."""
    print(f"\n[3] Stopping ETW session...")
    result = subprocess.run(
        ["logman", "stop", sessionName, "-ets"],
        capture_output=True, text=True, timeout=10
    )

    if result.returncode == 0:
        print("Session stopped")
    else:
        print(f"Stop error: {result.stderr[:200]}")

    # Check if trace file was created
    if os.path.exists(".etw_trace.etl"):
        size = os.path.getsize(".etw_trace.etl")
        print(f"Trace file: .etw_trace.etl ({size} bytes)")
        return ".etw_trace.etl"
    else:
        print("No trace file created")
        return None


def analyze_etw_trace(traceFile):
    """Analyze ETW trace for processor events."""
    if not traceFile or not os.path.exists(traceFile):
        return

    print(f"\n[4] Analyzing trace file...")

    # Try to convert using tracerpt
    result = subprocess.run(
        ["tracerpt", traceFile, "-o", "etw_events.csv", "-y"],
        capture_output=True, text=True, timeout=30
    )

    if result.returncode == 0:
        print("Trace converted to CSV")
        if os.path.exists("etw_events.csv"):
            with open("etw_events.csv") as f:
                lines = f.readlines()
            print(f"CSV has {len(lines)} lines")
            # Show unique event names
            events = set()
            for line in lines[2:]:  # Skip header
                parts = line.split(',')
                if len(parts) > 2:
                    events.add(parts[1].strip('"'))
            print(f"Unique events: {len(events)}")
            for e in sorted(events)[:20]:
                print(f"  {e}")
    else:
        print(f"Conversion error: {result.stderr[:200]}")


if __name__ == "__main__":
    print("=" * 60)
    print("ETW Trace Session Test")
    print("=" * 60)

    session = start_etw_session()
    if session:
        collect_etw_data(session, duration=3)
        trace = stop_etw_session(session)
        if trace:
            analyze_etw_trace(trace)

    # Cleanup
    for f in [".etw_trace.etl", "etw_events.csv"]:
        if os.path.exists(f):
            os.remove(f)

    print("\n" + "=" * 60)
    print("Test complete")
