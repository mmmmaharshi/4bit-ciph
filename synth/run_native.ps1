# QUARTET — Reproducible native synthesis (no docker required)
# Produces synthesis logs that reviewers can reproduce natively.
#
# Requirements: yowasp-yosys (pip install yowasp-yosys)
#
# Usage: pwsh synth/run_native.ps1

$ErrorActionPreference = "Stop"

$SYNTH_DIR = $PSScriptRoot
$ROOT = Split-Path $SYNTH_DIR -Parent
$HW_DIR = Join-Path $ROOT "hw"

# Find yowasp-yosys
$YOSYS = Join-Path (python -c "import sysconfig; print(sysconfig.get_path('scripts'))" 2>$null) "yowasp-yosys.exe"
if (-not (Test-Path $YOSYS)) { $YOSYS = "yowasp-yosys" }

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "QUARTET — Native Synthesis (Reproducible)" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Yosys: $YOSYS"
Write-Host ""

# 1. Generic cell stat (no liberty mapping — works natively)
Write-Host "[1/4] Generic cell count (technology-independent)..." -ForegroundColor Yellow
& $YOSYS -p "read_verilog quartet_logic.v; hierarchy -check -top quartet_round_logic; proc; opt; techmap; opt; stat" 2>&1 | Tee-Object -FilePath "yosys_native_generic.log" | Out-Null
Write-Host "      -> yosys_native_generic.log"

# 2. Write generic netlist (for area estimation)
Write-Host "[2/4] Writing generic netlist..." -ForegroundColor Yellow
& $YOSYS -p "read_verilog quartet_logic.v; hierarchy -check -top quartet_round_logic; proc; opt; techmap; opt; write_verilog -noattr synth_native_generic.v" 2>&1 | Out-Null
Write-Host "      -> synth_native_generic.v"

# 3. Iterative version (serial datapath)
Write-Host "[3/4] Iterative (serial) version..." -ForegroundColor Yellow
& $YOSYS -p "read_verilog quartet_logic.v; hierarchy -check -top quartet_iter_logic; proc; opt; techmap; opt; stat" 2>&1 | Tee-Object -FilePath "yosys_native_iter.log" | Out-Null
Write-Host "      -> yosys_native_iter.log"

# 4. Unrolled (fully parallel) version
Write-Host "[4/4] Unrolled (parallel) version..." -ForegroundColor Yellow
& $YOSYS -p "read_verilog quartet_logic.v; hierarchy -check -top quartet_enc_unrolled_logic; proc; opt; techmap; opt; stat" 2>&1 | Tee-Object -FilePath "yosys_native_unrolled.log" | Out-Null
Write-Host "      -> yosys_native_unrolled.log"

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "Native synthesis complete." -ForegroundColor Green
Write-Host "Logs: yosys_native_generic.log, yosys_native_iter.log, yosys_native_unrolled.log"
Write-Host "Netlist: synth_native_generic.v"
Write-Host ""
Write-Host "For post-P&R area/power (requires docker):" -ForegroundColor Cyan
Write-Host "  pwsh synth/run_postpnr.ps1"
Write-Host "======================================================================" -ForegroundColor Cyan
