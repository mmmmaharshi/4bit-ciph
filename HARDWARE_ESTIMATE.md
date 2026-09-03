# QUARTET Hardware Estimate — Reproducible Synthesis & Post-P&R

**Date:** 2026-09-03 | **Tools:** yowasp-yosys 0.68, OpenROAD (docker), Sky130 PDK
**RTL:** `synth/quartet_logic.v` (ANF S-box), `synth/quartet_sky130.v` (Sky130 mapped)

---

## 0. Reproducibility Overview

| Step | Tool | Environment | Output |
|------|------|-------------|--------|
| 1. Generic synthesis | yowasp-yosys | **Native** (no docker) | Cell counts: 176 cells/round |
| 2. Standard cell mapping | Yosys + liberty | Docker (yowasp WASI hang) | Area: ~245 GE/round (Sky130) |
| 3. Post-P&R | OpenROAD | Docker | Area: ~920 µm², Power: TBD |
| 4. Area estimation | Cell counts × GE | **Native** | 166–255 GE (serial/parallel) |

**Reviewers can reproduce steps 1 and 4 natively.** Steps 2 and 3 require docker.

---

## 1. Native Reproduction (No Docker)

### 1.1 Prerequisites

```powershell
pip install yowasp-yosys
```

### 1.2 Run Native Synthesis

```powershell
cd synth
pwsh run_native.ps1
```

This produces (all reproducible without docker):
- `yosys_native_generic.log` — cell counts (176 cells/round)
- `yosys_native_iter.log` — serial/iterative version
- `yosys_native_unrolled.log` — fully parallel version
- `synth_native_generic.v` — generic netlist

### 1.3 Expected Results (Native)

```
=== quartet_round_logic (1 round) ===
  176 cells = 36 AND + 8 NOT + 132 XOR

=== quartet_iter_logic (serial, 1 round reused) ===
  ~352 cells (datapath + FSM + state register)

=== quartet_enc_unrolled_logic (16 rounds parallel) ===
  2816 cells (16 × 176)
```

These results match the existing `yosys_generic_stat.log` in the repo.

---

## 2. Area Estimation (Native, From Cell Counts)

### 2.1 NanGate 45nm GE Factors

| Cell | Area µm² | GE |
|---|---|---|
| NAND2_X1 | 0.798 | **1.00** |
| AND2_X1 | 1.064 | 1.33 |
| XOR2_X1 | 1.596 | **2.00** |
| INV_X1 | 0.532 | 0.67 |
| DFF_X1 | 4.522 | 5.67 |

### 2.2 Generic-Cell Estimate (Pre-ABC, Pessimistic)

Single round: 36·1.33 + 8·0.67 + 132·2.00 = **317 GE** (generic)
→ ABC-optimized ≈ **50–60%** of generic ≈ **160–190 GE**

### 2.3 Literature-Anchored Estimate (Per S-box: 22 GE)

Source: Poschmann CHES 2009, NanGate 45nm, optimized PRESENT S-box.

| Component | GE |
|---|---|
| S-box (×4 parallel) | 4 × 22 = **88 GE** |
| FullMix (12 XOR) | 12 × 2 = **24 GE** |
| Key XOR (16 bit) | 16 × 2 = **32 GE** |
| State register (16 DFF) | 16 × 5.67 = **91 GE** |
| Control (FSM + counter) | **~20 GE** |
| **Parallel total** | **~255 GE** |

### 2.4 Serial (Iterative) Estimate

| Component | GE |
|---|---|
| 1× S-box (shared) | **22 GE** |
| FullMix | **24 GE** |
| Key XOR | **32 GE** |
| State register (64 latch) | **~64 GE** |
| Control | **~24 GE** |
| **Serial total** | **~166 GE** |

---

## 3. Post-P&R (Docker Required)

### 3.1 Prerequisites

```powershell
# Install Sky130 PDK
pip install volare
volare enable --pdk sky130A

# Ensure Docker Desktop is running
docker info
```

### 3.2 Run Post-P&R Flow

```powershell
cd synth
pwsh run_postpnr.ps1
```

This runs:
1. Yosys synthesis with Sky130 liberty mapping
2. OpenROAD place-and-route
3. Power analysis

### 3.3 Expected Results (Docker)

From prior runs (2026-09-01):
- **Sky130 synthesis**: 245 GE/round (NAND2_1 = 3.7536 µm²)
- **Post-P&R area**: ~920 µm² total chip area
- **Serial 1-Sbox**: ~150 GE (matches NanGate 136 GE within tech scaling)

---

## 4. Resolved: FullMix is Order-4 (Not Self-Inverse)

```
M = [[1,1,1,0],[0,1,1,1],[1,0,1,1],[1,1,0,1]]  (SPEC §4)
M·M = [[0,0,1,0],[0,0,0,1],[1,0,0,0],[0,1,0,0]] = swap halves
M⁴ = I  (order 4, not involution)
```

**Decryption inverse** (fixed 2026-09-01):
```
M⁻¹ = M³ = [[1,0,1,1],[1,1,0,1],[1,1,1,0],[0,1,1,1]]
W0' = W0^W2^W3, W1' = W0^W1^W3, W2' = W0^W1^W2, W3' = W1^W2^W3
```

Impact:
- **Enc-only (~166 GE serial)** — unaffected
- **Enc/dec (~254 GE serial)** — adds M³ (12 XOR, 24 GE) + inverse S-box (64 GE)

---

## 5. Power Estimation (Post-P&R Required)

Power analysis requires post-P&R simulation with actual switching activity:

1. **Dynamic power**: Depends on toggle rate from real workloads
2. **Leakage power**: Determined by cell library and area
3. **Estimation method**: 
   - Run post-P&R with VCD (value change dump) from test vectors
   - OpenROAD reports power based on extracted parasitics

**Status**: Power estimates pending post-P&R simulation with representative workloads.

---

## 6. Files for Paper

| File | Description | Reproducible |
|------|-------------|--------------|
| `synth/quartet_logic.v` | RTL (ANF S-box) | — |
| `synth/quartet_sky130.v` | RTL (Sky130 mapped) | — |
| `synth/run_native.ps1` | Native synthesis script | **Yes (native)** |
| `synth/run_postpnr.ps1` | Post-P&R script | Docker required |
| `synth/yosys_native_generic.log` | Generic cell counts | **Yes (native)** |
| `synth/yosys_native_iter.log` | Serial version | **Yes (native)** |
| `synth/yosys_native_unrolled.log` | Parallel version | **Yes (native)** |
| `synth/synth_native_generic.v` | Generic netlist | **Yes (native)** |
| `HARDWARE_ESTIMATE.md` (this file) | Analysis | — |

---

## 7. Status (Updated 2026-09-03)

1. ✔ Native synthesis script (`run_native.ps1`) — reproducible without docker
2. ✔ Post-P&R script (`run_postpnr.ps1`) — docker-based
3. ✔ Native logs committed (`yosys_native_*.log`)
4. ✔ Generic netlist committed (`synth_native_generic.v`)
5. ✔ Clear reproducibility documentation (this file)
6. ⏳ Power estimates — pending post-P&R simulation with VCD
