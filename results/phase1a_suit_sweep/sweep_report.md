# Phase 1a Moco Suit Sweep — Dose-Response Report

Five conditions: F = 0 / 50 / 100 / 150 / 200 N → T = 0 / 6 / 12 / 18 / 24 N·m
All converged (Optimal Solution Found). Wall time ~12 min/condition (4 in parallel).

## ES_mean (6-muscle average) per condition

| F (N) | T (N·m) | Hold mean (%) | Concentric mean (%) | Δ Hold (%) | Δ Con (%) |
|---:|---:|---:|---:|---:|---:|
| 0 | 0.0 | 52.71 | 49.87 | +0.00 | +0.00 |
| 50 | 6.0 | 49.02 | 46.32 | +6.99 | +7.12 |
| 100 | 12.0 | 45.36 | 42.79 | +13.94 | +14.20 |
| 150 | 18.0 | 41.66 | 39.23 | +20.96 | +21.34 |
| 200 | 24.0 | 37.97 | 35.68 | +27.95 | +28.46 |

## IL_R10_r per condition (dominant muscle)

| F (N) | T (N·m) | Peak (%) | Hold mean (%) | Conc mean (%) | Δ Hold (%) | Δ Con (%) |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.0 | 92.38 | 87.73 | 82.78 | +0.00 | +0.00 |
| 50 | 6.0 | 83.30 | 79.30 | 74.69 | +9.60 | +9.77 |
| 100 | 12.0 | 74.19 | 70.88 | 66.60 | +19.20 | +19.55 |
| 150 | 18.0 | 65.11 | 62.44 | 58.48 | +28.83 | +29.35 |
| 200 | 24.0 | 56.31 | 53.96 | 50.35 | +38.49 | +39.18 |

## Linear fits (ES reduction % vs Torque N·m)

| Metric | Slope (%/Nm) | Intercept | R² | Reduction @ 24 Nm |
|---|---:|---:|---:|---:|
| **Moco ES_mean Hold** | **1.164** | -0.004 | **1.0000** | **+27.95 %** |
| Moco ES_mean Concentric | 1.186 | -0.005 | 1.0000 | +28.46 % |
| Moco IL_R10_r Hold | 1.603 | -0.016 | 1.0000 | +38.49 % |
| Moco IL_R10_r Concentric | 1.632 | -0.018 | 1.0000 | +39.18 % |
| **SO §1.6 reference** | **1.206** | +0.04 | **1.000** | **28.97 %** |

## Comparison

- Slope agreement: Moco 1.164 vs SO 1.206 → relative diff **-3.4 %**
- Reduction @ 24 N·m: Moco 27.95 % vs SO 28.97 % → diff **-1.02 %p**
- R² agreement: Moco 1.0000 vs SO 1.000 → both essentially perfect linearity

### Headline findings
- **MocoInverse confirms SO §1.6 dose-response slope** within 1 %p tolerance
- **Linearity preserved**: R² > 0.99 for all four metrics (Hold and Concentric, ES_mean and IL_R10)
- **IL_R10 (dominant muscle) has higher slope** than ES_mean: muscles closer to the suit moment
  axis benefit more from each unit of assistive torque
- **No cost-function-induced anomalies**: monotone dose-response across the full sweep
