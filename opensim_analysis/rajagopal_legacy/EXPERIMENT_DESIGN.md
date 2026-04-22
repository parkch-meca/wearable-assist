# Wearable Exosuit Musculoskeletal Analysis — Experiment Design

## Objective
Quantify muscle activation reduction during stoop-lift tasks when wearing SMA fabric-actuated exosuit,
across diverse subject populations.

## Model
**Rajagopal2016** (OpenSim 4.5.2)
- 39 DoF, 80 lower-limb muscles, 17 upper-body torque actuators
- Upper-body torque actuators serve as proxy for erector spinae, deltoid, biceps groups
- Optional: Merge Christophy 2012 lumbar muscles for detailed erector spinae analysis

## Motion Data
**BONES-SEED** soma_uniform BVH → OpenSim .mot conversion
- 377 unique stoop motions (mirrored excluded), 748 total clips
- 120 fps, ~29s average duration
- Pipeline: `convert_bvh_to_opensim.py`

---

## Independent Variables (5 factors)

### 1. Sex (2 levels)
| Level | Body mass (kg) | Height (cm) | Model scaling |
|-------|---------------|-------------|---------------|
| Male | 78 | 175 | Rajagopal default |
| Female | 62 | 162 | Scale factors from anthropometry |

### 2. Age group (3 levels)
| Level | Age range | Muscle strength factor | Max isometric force multiplier |
|-------|-----------|----------------------|-------------------------------|
| Young | 20-35 | 1.0 (reference) | 1.0 |
| Middle | 36-55 | 0.85 | 0.85 |
| Senior | 56-70 | 0.65 | 0.65 |

### 3. Body type (3 levels)
| Level | BMI range | Mass scaling | Segment inertia scaling |
|-------|-----------|-------------|------------------------|
| Slim | 18-22 | 0.85 | 0.85 |
| Average | 22-27 | 1.0 | 1.0 |
| Heavy | 27-35 | 1.25 | 1.30 |

### 4. Lift load (3 levels)
| Level | Load mass (kg) | Applied as | Location |
|-------|---------------|-----------|----------|
| Light | 3 | External force on hands | Wrist bodies |
| Medium | 8 | External force on hands | Wrist bodies |
| Heavy | 15 | External force on hands | Wrist bodies |

### 5. Suit assist level (5 levels)
| Level | Assist ratio | Config | Back torque | Shoulder torque |
|-------|-------------|--------|-------------|-----------------|
| No suit | 0% | none | 0 Nm | 0 Nm |
| Minimal | 15% | full_suit | ~4 Nm | ~3 Nm |
| Moderate | 30% | full_suit | ~8 Nm | ~6 Nm |
| Strong | 50% | full_suit | ~13 Nm | ~10 Nm |
| Maximum | 75% | full_suit_hip | ~20 Nm | ~15 Nm |

**Total conditions:** 2 × 3 × 3 × 3 × 5 = **270**

---

## Dependent Variables (per condition)

### Primary outcomes
1. **Peak joint torques** (Nm) — lumbar, hip, knee, shoulder, elbow
2. **Mean absolute joint torques** (Nm) — same joints
3. **Peak muscle activations** (0-1) — 80 lower-limb muscles via Static Optimization
4. **Mean muscle activations** (0-1) — same muscles

### Secondary outcomes
5. **Torque reduction ratio** — (no_suit - suited) / no_suit × 100%
6. **Peak-to-mean ratio** — indicates sustained vs. burst loading
7. **Bilateral symmetry index** — |left - right| / mean(left, right)

### Key muscle groups for reporting
| Group | Muscles | Role in stoop |
|-------|---------|---------------|
| Erector spinae | `lumbar_ext` actuator | Trunk extension |
| Gluteus maximus | glmax1/2/3_r/l | Hip extension |
| Hamstrings | bflh_r/l, semimem_r/l, semiten_r/l | Hip ext + knee flex |
| Quadriceps | recfem_r/l, vasint/lat/med_r/l | Knee extension |
| Deltoid | `shoulder_flex` actuator | Arm elevation |
| Biceps | `elbow_flex` actuator | Elbow flexion |

---

## Model Scaling Strategy

### Per-condition model generation
```python
# Pseudocode for model variant creation
for sex in ['male', 'female']:
    for age in ['young', 'middle', 'senior']:
        for body_type in ['slim', 'average', 'heavy']:
            model = load_base_model('Rajagopal2016.osim')
            apply_anthropometric_scaling(model, sex, body_type)
            apply_strength_scaling(model, age)
            for suit_config in assist_levels:
                add_suit_actuators(model, suit_config)
                save_model(model, f"model_{sex}_{age}_{body_type}_{suit_config}.osim")
```

### Anthropometric scaling
- **Height scaling**: uniform geometric scale factor on all segments
- **Mass scaling**: non-uniform — torso mass scales more than limbs for "heavy" type
- **Segment lengths**: proportional to height ratio
- **Muscle parameters**: max_isometric_force scales with (cross_section_area × age_factor)

### Scaling source
Use OpenSim Scale Tool with virtual markers placed at standard anthropometric landmarks.
Scale factors derived from:
- Gordon et al. (1989) anthropometric survey
- De Leva (1996) segment inertia parameters

---

## Analysis Pipeline

### Per motion clip (stoop) × per condition
```
1. Load scaled model + suited variant
2. Load .mot file (BVH → OpenSim converted)
3. Run Inverse Dynamics → joint torques (.sto)
4. Run Static Optimization → muscle activations (.sto)
5. Extract peak/mean metrics → append to results DataFrame
```

### Computational strategy

**Hardware:** 28-core workstation, RTX PRO 6000 96GB
- ID: ~0.6s per 600-frame clip
- Static Optimization: ~30s per clip (estimated)
- Per condition: ~31s
- 270 conditions × 10 representative clips = 2,700 runs
- Sequential: ~23 hours
- **Parallel (28 cores): ~50 minutes**

### Parallelization plan
```python
from multiprocessing import Pool

def run_single_condition(args):
    model_path, mot_path, condition_id = args
    # ... ID + StaticOpt + extract metrics
    return metrics_dict

with Pool(28) as pool:
    results = pool.map(run_single_condition, all_conditions)
```

### Motion clip selection (10 representative from 377)
1. Select by peak hip flexion angle: min, p25, p50, p75, max
2. Select by duration: short (<15s), medium (15-25s), long (>25s)
3. Include 1 injured variant, 1 relaxed variant
4. Total: 10 clips cover the range of stoop kinematics

---

## Expected Outputs

### Data files
- `/data/opensim_analysis/results/all_conditions.csv` — 270 × 10 = 2,700 rows × ~50 metric columns
- `/data/opensim_analysis/results/summary_by_condition.csv` — 270 rows (averaged over clips)
- `/data/opensim_analysis/results/muscle_activations/` — per-condition .sto files

### Figures (for paper/marketing)
1. **Torque reduction heatmap** — assist_level × body_type × joint
2. **Muscle activation bar chart** — key muscles, no-suit vs. 30% assist vs. 50% assist
3. **Sex × age interaction plot** — lumbar torque reduction across demographics
4. **Stoop phase analysis** — time series of lumbar/hip torque during bend-hold-lift cycle
5. **Full-body animation** — OpenSim visualization frames at key poses

### Statistical analysis
- 3-way ANOVA: sex × age × body_type on torque reduction
- Post-hoc Tukey HSD for pairwise comparisons
- Effect sizes (Cohen's d) for suit vs. no-suit
- 95% CI for torque reduction ratios

---

## Timeline

| Phase | Task | Duration |
|-------|------|----------|
| 1 | SOMA BVH download + conversion | 1-2 days (download) |
| 2 | Model scaling (18 variants) | 2 hours |
| 3 | Suited model generation (270 variants) | 30 min |
| 4 | Batch ID + StaticOpt (2,700 runs) | ~1 hour (28-core parallel) |
| 5 | Result aggregation + statistics | 1 hour |
| 6 | Figure generation | 2 hours |
| **Total** | | **~1 day after SOMA download** |

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| SOMA BVH joint names don't match expected | Conversion fails | Auto-detect + fallback to raw BVH parser |
| Rajagopal upper-body torque actuators insufficient | No muscle-level detail for back/shoulder | Merge Christophy lumbar spine muscles |
| Static Optimization convergence failure | Missing muscle activations | Fall back to ID-only analysis (torques) |
| 270 model variants = large disk usage | ~50GB | Store only results, regenerate models on-fly |
| G1 vs SOMA angle range mismatch | Validation unclear | Cross-check G1 and SOMA angles for same clip |
