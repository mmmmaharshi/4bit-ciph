#!/bin/bash
# QUARTET — Sky130 OpenLane synthesis (Path 2 breakthrough)
# 1. Yosys quick area (no PDK): yowasp-yosys -p "read_verilog quartet_logic.v; synth -top quartet_round_logic; stat"
# 2. Sky130 GDS: docker run -v $PWD:/work ghcr.io/the-openroad-project/openlane:latest flow.tcl -design quartet_sky130
set -e
echo "=== Yosys quick (NanGate already in HARDWARE_ESTIMATE.md) ==="
yowasp-yosys -p "read_verilog quartet_logic.v; hierarchy -check -top quartet_round_logic; proc; opt; techmap; opt; stat"
echo ""
echo "=== Sky130 (needs docker + PDK) ==="
echo "docker run --rm -v $PWD:/work -v \$PDK_ROOT:\$PDK_ROOT -e PDK=sky130A ghcr.io/efabless/openlane:latest flow.tcl -design quartet_sky130 -tag quartet"
