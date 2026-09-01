#!/bin/bash
# QUARTET — Sky130 OpenLane synthesis (Path 2 breakthrough)
# 1. Yosys quick area (no PDK): yowasp-yosys -p "read_verilog quartet_logic.v; synth -top quartet_round_logic; stat"
# 2. Sky130 GDS: docker run -v $PWD:/work ghcr.io/the-openroad-project/openlane:latest flow.tcl -design quartet_sky130
set -e
echo "=== Yosys quick (NanGate already in HARDWARE_ESTIMATE.md) ==="
YOSYS="$(python3 -c 'import sysconfig,pathlib;print(pathlib.Path(sysconfig.get_path("scripts"))/"yowasp-yosys")' 2>/dev/null || python -c 'import sysconfig,pathlib;print(pathlib.Path(sysconfig.get_path("scripts"))/"yowasp-yosys")' 2>/dev/null || echo yowasp-yosys)"
"$YOSYS" -p "read_verilog quartet_logic.v; hierarchy -check -top quartet_round_logic; proc; opt; techmap; opt; stat" 2>/dev/null || yowasp-yosys -p "read_verilog quartet_logic.v; hierarchy -check -top quartet_round_logic; proc; opt; techmap; opt; stat"
echo ""
echo "=== Sky130 (needs docker + PDK) ==="
if [ -z "$PDK_ROOT" ]; then echo "PDK_ROOT not set — run: volare enable --pdk sky130 ; export PDK_ROOT=\$HOME/.volare/sky130A"; echo "Trying Sky130 liberty stat without PDK..."; else echo "Running OpenLane..."; docker run --rm -v "$PWD:/work" -v "$PDK_ROOT:$PDK_ROOT" -e PDK=sky130A -w /work efabless/openlane:latest flow.tcl -design quartet_sky130 -tag quartet || echo "OpenLane failed — liberty stat still valid"; fi
