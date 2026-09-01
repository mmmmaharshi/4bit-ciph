# QUARTET — Sky130 synth (Windows)
# Yosys quick area already proven: 176 cells (36 AND + 8 NOT + 132 XOR)
$YOSYS = Join-Path (python -c "import sysconfig; print(sysconfig.get_path('scripts'))" 2>$null) "yowasp-yosys.exe"
if (-not (Test-Path $YOSYS)) { $YOSYS = "yowasp-yosys" }
Write-Host "=== Yosys quick (NanGate) ==="
& $YOSYS -p "read_verilog quartet_logic.v; hierarchy -check -top quartet_round_logic; proc; opt; techmap; opt; stat"
Write-Host ""
Write-Host "=== Sky130 (needs docker + PDK) ==="
if (-not $env:PDK_ROOT) { Write-Host "PDK_ROOT not set — run: pip install volare; volare enable --pdk sky130; `$env:PDK_ROOT=`$HOME/.volare/sky130A" }
else { docker run --rm -v "${PWD}:/work" -v "${env:PDK_ROOT}:${env:PDK_ROOT}" -e PDK=sky130A -w /work efabless/openlane:latest flow.tcl -design quartet_sky130 -tag quartet }
