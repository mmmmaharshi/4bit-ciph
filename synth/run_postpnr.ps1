# QUARTET — Post-P&R area/power estimation (requires docker)
# Uses OpenROAD-flow-scripts via docker for place-and-route and power analysis.
#
# Prerequisites:
#   - Docker Desktop installed and running
#   - Sky130 PDK via volare: pip install volare; volare enable --pdk sky130A
#
# Usage: pwsh synth/run_postpnr.ps1

$ErrorActionPreference = "Stop"

$SYNTH_DIR = $PSScriptRoot
$ROOT = Split-Path $SYNTH_DIR -Parent

# Check docker
try {
    docker info 2>$null | Out-Null
} catch {
    Write-Host "ERROR: Docker not available. Install Docker Desktop." -ForegroundColor Red
    exit 1
}

# Check PDK
$PDK_ROOT = $env:PDK_ROOT
if (-not $PDK_ROOT) {
    $PDK_ROOT = Join-Path $HOME ".volare\sky130A"
    if (-not (Test-Path $PDK_ROOT)) {
        Write-Host "PDK not found. Install with:" -ForegroundColor Yellow
        Write-Host "  pip install volare"
        Write-Host "  volare enable --pdk sky130A"
        exit 1
    }
    $env:PDK_ROOT = $PDK_ROOT
}

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "QUARTET — Post-P&R Area/Power Estimation (Docker)" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "PDK_ROOT: $PDK_ROOT"
Write-Host ""

# Option 1: Yosys with Sky130 liberty (synthesis + area, no P&R)
Write-Host "[1/3] Sky130 synthesis (Yosys + liberty mapping)..." -ForegroundColor Yellow
$libPath = Join-Path $PDK_ROOT "libs.ref\sky130_fd_sc_hd\lib\sky130_fd_sc_hd__tt_025C_1v80.lib"
if (Test-Path $libPath) {
    $yosysCmd = "read_verilog quartet_logic.v; hierarchy -check -top quartet_round_logic; proc; opt; synth -top quartet_round_logic; dfflibmap -liberty $libPath; abc -liberty $libPath; stat -liberty $libPath"
    docker run --rm -v "${PWD}:/work" -w /work efabless/openlane:latest yosys -p $yosysCmd 2>&1 | Tee-Object -FilePath "yosys_sky130_postsynth.log"
    Write-Host "      -> yosys_sky130_postsynth.log"
} else {
    Write-Host "      Sky130 liberty not found, skipping."
}

# Option 2: Full OpenROAD P&R flow
Write-Host ""
Write-Host "[2/3] Full OpenROAD P&R flow (area + power)..." -ForegroundColor Yellow
Write-Host "      This runs the full OpenROAD flow including placement, routing,"
Write-Host "      and power analysis. Results in openlane/results/"

# Copy design to openlane directory structure
$openlaneDir = Join-Path $SYNTH_DIR "openlane\quartet"
if (-not (Test-Path $openlaneDir)) {
    New-Item -ItemType Directory -Path $openlaneDir -Force | Out-Null
}
Copy-Item "quartet_sky130.v" $openlaneDir -Force

# Run OpenROAD flow via docker
docker run --rm -v "${PWD}:/work" -v "${PDK_ROOT}:${PDK_ROOT}" -e PDK=sky130A -w /work efabless/openlane:latest bash -c "cd openlane && ./flow.tcl -design quartet -tag quartet_pnr" 2>&1 | Tee-Object -FilePath "openlane_pnr.log"

# Extract results
Write-Host ""
Write-Host "[3/3] Extracting results..." -ForegroundColor Yellow
$resultsDir = Join-Path $SYNTH_DIR "openlane\quartet\results\quartet_pnr"
if (Test-Path $resultsDir) {
    Get-ChildItem $resultsDir -Recurse | Select-Object Name, Length
    Write-Host "      -> openlane/results/"
} else {
    Write-Host "      Results directory not found. Check openlane_pnr.log for errors."
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "Post-P&R complete." -ForegroundColor Green
Write-Host "Logs: yosys_sky130_postsynth.log, openlane_pnr.log"
Write-Host "======================================================================" -ForegroundColor Cyan
