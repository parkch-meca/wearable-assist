# Wearable Assist Research Roadmap

## Phase 1 (Complete) — Full-Body Musculoskeletal Analysis

- **Model**: Rajagopal2016 + bilateral erector spinae (82 muscles, OpenSim 4.5.2)
- **Motion**: BONES-SEED 748 stoop clips, 10 representative SOMA BVH @ 120fps
- **Design**: 270 conditions (2 sex × 3 age × 3 body × 3 load × 5 suit force)
- **Computation**: 2,700 simulations in 70 seconds (24-core parallel)
- **Key Results** (20kg, 200N SMA suit):
  - Erector Spinae (lumbar): **16.1% reduction**
  - Deltoid (shoulder): **46.0% reduction**
  - Biceps (elbow): **37.3% reduction**
- **Validation**: Literature-consistent (de Looze 2016, Koopman 2019, Huysamen 2018)
- **Deliverables**: 7 figures, infographic, 7-slide PPTX, REPORT.md

## Phase 2 (Planned) — Motion Diversification

- Add side bend, carry, reach, overhead motions from BONES-SEED
- Motion-specific muscle activation profiles
- Cumulative fatigue modeling over work shifts (8hr simulation)
- Comparison: stoop vs squat lift strategies

## Phase 3 (Planned) — Foundation Model

- Input: subject demographics + task parameters → Output: predicted muscle reduction
- Train on Phase 1+2 simulation database (~10,000+ conditions)
- SONIC-based whole-body control + assistive force conditioning
- Target: International journal publication (e.g., Journal of Biomechanics)

## Phase 4 (Future) — Hardware Validation

- EMG comparison: simulation vs measured muscle activation
- SMA actuator bench test: force-displacement characterization
- Pilot study: 10 subjects × 3 tasks × 3 suit conditions
