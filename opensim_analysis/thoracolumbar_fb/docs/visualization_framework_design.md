# Visualization Framework Design
# Step 1.4 — Architecture (Design Only, No Implementation)
# Date: 2026-04-29

---

## 0. Purpose and Scope

This document defines the **permanent** visualization and video framework for the wearable-assist project.
It covers all planned tasks (Stoop, Box, Squat, Walk, Patient Transfer) and supports two simultaneous
delivery targets: **YouTube/web** and **journal supplementary material**.

This is a design-only document. No scripts are executed here. Implementation begins in Step 2 once
the four Step 1 architecture reports are integrated.

---

## 1. Video Specification

### 1.1 Resolution and codec tiers

| Tier | Resolution | FPS | Codec | Use case |
|------|-----------|-----|-------|----------|
| Verification | 1280 x 720 | 30 | h264 (CRF 23) | Internal check, fast render |
| Standard (default) | 1920 x 1080 | 30 | h264 (CRF 17) | YouTube upload, journal supplement |
| Archive | 3840 x 2160 | 30 | h265 (CRF 18) | Long-term storage, future reuse |

**Rationale for 1080p / 30fps default:**
- YouTube HD minimum is 1280x720. 1080p gives one tier of headroom.
- 60fps doubles file size without scientific benefit for slow biomechanics motion (~5 s total).
- h264 CRF 17 yields near-lossless quality at manageable file size (~15-30 MB for a 30-s clip).
- h265 archive is generated only for the final accepted version of each task.

### 1.2 Duration conventions

| Content type | Duration | Notes |
|---|---|---|
| Stage 4 verification clip | 5 s (1x speed) | Same as motion file duration |
| Suit comparison clip | 3-5 s (eccentric+lift only) | Moco range t=1.0-4.0 for box task |
| YouTube full-motion clip | 30-60 s | Slow-motion (0.3x) + title cards |
| Loop preview | 5-8 s | For presentations, looping |

Slow-motion encoding: motion is rendered at full speed (30fps), then ffmpeg `-filter:v "setpts=3.0*PTS"`
applies the slow-down. This avoids re-rendering.

### 1.3 Audio

No audio for scientific videos. Burned-in subtitle overlay (Section 6) replaces narration.
YouTube description carries full methodology text.

### 1.4 ffmpeg encode command (standard)

```bash
ffmpeg -y -loglevel warning \
  -framerate 30 \
  -i /tmp/{task}_frames/frame_%04d.png \
  -c:v libx264 -pix_fmt yuv420p \
  -crf 17 -preset medium \
  -movflags +faststart \
  /data/opensim_results/video/{task}_{version}.mp4
```

Output copy to repo: `/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/videos/`

---

## 2. ES Color Overlay — Meaningful Gradient

### 2.1 Color schema

The color encodes ES (erector spinae) activation as a continuous gradient on rendered muscle lines.
Colors are chosen to be perceptible under colorblind conditions (deuteranopia safe for the red-orange
range used here, tested against Coblis simulator).

| Activation | Hex | Name | Meaning |
|---|---|---|---|
| 100% | #8B0000 | Dark red | Maximum / saturated |
| 75% | #CC2200 | Red | High load |
| 50% | #FF6600 | Orange | Moderate load |
| 25% | #FFB300 | Amber | Low-moderate load |
| 10% | #FFD700 | Gold-yellow | Low load |
| 0% | #909090 | Mid-grey | Inactive |

In PyVista this is implemented as a custom colormap (LinearSegmentedColormap) mapped to [0.0, 1.0]
muscle activation scalars. The scalar bar is always shown in journal figures; suppressed in video.

### 2.2 Critical constraint: 200 N·m scenario is excluded from comparison videos

**Lesson learned (Phase 2.C.4 v1 analysis):**
- B_suit200 (200 N·m) drives IL_R10_r from ~100% to ~0.8% — a 99 %p drop.
- This is not representative of the real suit (24 N·m, 28% reduction).
- Showing 100% → 0% in a comparison video creates a misleading impression.

**Rule:** Suit comparison videos use **B_noload vs B_suit24** (or the closest available condition
to 24 N·m). The 28% reduction (87.7% → 63% for IL_R10_r) produces an orange-to-red gradient
change that is scientifically honest and visually meaningful.

If B_suit24 is not available as a direct condition, interpolate from the dose-response regression
(slope = -0.129 %/N·m, R² = 0.94 from Phase 2.C.4 v5).

### 2.3 Reference numbers for overlay text

From Phase 1a (stoop, v5 motion, MocoInverse):
- IL_R10_r: 87.7% (Suit OFF) → 63.0% (Suit ON 24 N·m) → delta -24.7 %p (-28%)

From Phase 2.C.4 v5 (box, v11b motion):
- ES mean: dose-response slope -0.129 %/N·m at grasp peak
- Reserve actuator < 8 N·m in v5 solution (acceptable)

These numbers are fixed reference points. Any future analysis that changes them must update
this document before re-rendering comparison videos.

---

## 3. Suit ON/OFF Comparison Layout

### 3.1 Recommended layout: Option A (Side-by-side)

```
+----------------------------+----------------------------+
|  SUIT OFF  |  B_noload     |  SUIT ON   |  B_suit24     |
|                            |                            |
|   3D body + ES lines       |   3D body + ES lines       |
|   (red-orange activation)  |   (amber activation)       |
|                            |                            |
|  [1920 x 700 px total top panel, 960 px each side]     |
+----------------------------+----------------------------+
|  IL_R10_r time series  (left half)                     |
|  ES mean bar + key stats   (right half)                 |
|  [1920 x 200 px bottom panel]                          |
+-----------------------------------------------------------+
Total: 1920 x 900 px
```

This layout already exists in `render_box_v11b_suit_comparison.py` for the B_noload/B_suit200
comparison. The Step 2 implementation will change the suit condition from 200 N·m to 24 N·m
(or nearest available) and update the annotation text accordingly.

### 3.2 Camera angle for comparison

Single shared camera, 3-quarter view (position [-2.2, 0.8, 3.0], focal [0.2, 0.0, 0.0]):
- Shows both spine and lower limb simultaneously.
- Avoids the pure sagittal view where ES lines are hidden behind the spine.
- Consistent with Stage 4 grid 3-quarter column.

### 3.3 Text overlay specification

Top-left of each panel (PyVista `add_text`, font='courier', size=16):
```
SUIT OFF  |  B_noload           <- red badge
SUIT ON   |  B_suit24 (24 N·m) <- green badge
```

Bottom panel annotation (matplotlib):
```
IL_R10_r: 87.7% → 63.0%  (Delta -24.7 %p,  -28%)
ES mean dose-response: -0.129 %/N·m  (R² = 0.94)
Reference: Hu 2026  [14.9–28.6% range]
```

### 3.4 Option B and C (non-default)

Option B (single view + time series panel below): use when only one motion angle is needed,
e.g., a figure for a poster where space is limited.

Option C (heat-map overlay on body surface): requires mesh-based activation mapping, not
currently implemented. Defer to Step 3+ once mesh rendering pipeline is stable.

---

## 4. Consistent Template Across All Tasks

Every video, regardless of task type, uses the same visual template so viewers recognize
the project style immediately.

### 4.1 On-screen elements (fixed positions)

```
+-- Upper-left --------------------------------+
|  Task label (Arial Bold 18pt)               |
|  e.g., "Box Lift  |  Semi-squat  |  20 kg" |
+-- Upper-right --------------------------------+
|  Condition badge (Arial 16pt)               |
|  e.g., "Suit OFF" (red) / "Suit ON" (green)|
+-- Lower strip (full width, 40px) ------------+
|  Phase progress bar                         |
|  [Eccentric]---[Grasp]---[Concentric]---[Carry]
|  Current time tick                          |
+----------------------------------------------+
```

### 4.2 Phase progress bar color coding

| Phase | Color | Timing (box task) | Timing (stoop task) |
|---|---|---|---|
| Quiet standing | #AAAAAA | t = 0.0-0.5 s | t = 0.0-0.5 s |
| Eccentric | #1565C0 (blue) | t = 0.5-2.0 s | t = 0.5-2.5 s |
| Grasp / peak | #CC2222 (red) | t = 2.0-2.5 s | t = 2.5-2.8 s |
| Concentric | #2E7D32 (green) | t = 2.5-4.0 s | t = 2.8-4.5 s |
| Carry / recovery | #6A1B9A (purple) | t = 4.0-5.0 s | t = 4.5-5.0 s |

These phase boundaries are task-specific and are defined in a per-task config dict
(see Section 9.3, implementation spec).

### 4.3 Body color

- Bone/skeleton mesh: #D4C5A9 (warm ivory), opacity 0.95, smooth_shading=True
- Skeleton stick figure (Stage 4 / lightweight): #3A6EA5 (blue-grey)
- Joint spheres: #2E86AB (bright blue)
- Box object: #C17F24 (amber-brown), opacity 0.88, show_edges=True
- Ground plane: #CCCCCC (light grey), opacity 0.5

### 4.4 Background

- Video (dark): #1C1C2E (very dark navy) — cinema-style, ES lines pop
- Stage 4 grid (light): #F8F8F8 (off-white) — print-friendly, journal-safe

---

## 5. Stage 4 Grid Protocol (Permanent)

### 5.1 Standard specification

Every new motion version goes through Stage 4 before any Moco analysis. No exceptions.

```
Output: {motion_name}_stage4_grid.png  (5 rows x 3 cols composite)
        {motion_name}_stage4_t{X.X}_{view}.png  (15 individual frames)

Location:
  docs/images/phase2_box/    for box-type tasks
  docs/images/phase1a_stoop/ for stoop tasks (new, to be created)
  docs/images/phase2_squat/  for squat tasks (future)
  docs/images/phase2_walk/   for walk tasks (future)
  docs/images/phase2_xfer/   for patient transfer (future)

Resolution: 150 dpi, individual panels 800x800 px
```

### 5.2 Standard frame times

```python
FRAMES = [
    (0.0,  'Quiet Standing'),
    (1.5,  'Eccentric Mid'),
    (2.0,  'Grasp / Peak Load'),
    (3.0,  'Concentric Mid'),
    (5.0,  'Carry / Recovery'),
]
```

For tasks shorter than 5 s, the last frame uses the actual end time.
For tasks longer than 5 s (e.g., walk cycle), frames are scaled proportionally.

### 5.3 Standard views

```python
VIEWS = {
    'sagittal': {
        'position': (0.0, 0.4, 4.0),
        'focal_point': (0.0, 0.0, 0.0),
        'up': (0.0, 1.0, 0.0),
    },
    'anterior': {
        'position': (-4.0, 0.4, 0.0),
        'focal_point': (0.0, 0.0, 0.0),
        'up': (0.0, 1.0, 0.0),
    },
    '3quarter': {
        'position': (-2.2, 0.8, 3.0),
        'focal_point': (0.2, 0.0, 0.0),
        'up': (0.0, 1.0, 0.0),
    },
}
```

These camera positions are FIXED across all tasks. Changing them breaks cross-task
visual comparability. Adjust only if a new task (e.g., walking) requires a wider field.

### 5.4 Self-verification checklist (automated in script output)

After grid generation, the script prints and saves a checklist. Items are evaluated
by reading each PNG with the Read tool.

```
Stage 4 Self-Verification Checklist — {motion_name}

POSTURE:
[ ] P1: t=0.0 — upright stance, no lean
[ ] P2: t=1.5 — trunk bending, pelvis tilting forward
[ ] P3: t=2.0 — max flexion, hands at box sides (NOT top)
[ ] P4: t=3.0 — trunk rising, box ascending
[ ] P5: t=5.0 — upright, box at chest height (NOT dangling)

FEET (box task only):
[ ] F1: Feet visible on ground plane in all frames
[ ] F2: No foot embedding below ground plane (visual check)
[ ] F3: Feet do not move toward box between frames

ARMS / HANDS (box task only):
[ ] A1: No X-crossed arms at any frame
[ ] A2: t=2.0 — hands at box SIDES not top
[ ] A3: t=5.0 — hands still holding box sides, box not floating free

BOX (box task only):
[ ] B1: Box on ground at t=0, 1.5, 2.0
[ ] B2: Box ascending between t=2.0 and t=3.0
[ ] B3: Box at chest height at t=5.0
[ ] B4: No knee-box penetration (knee does not pass through box)
[ ] B5: Box not floating above ground before grasp

GENERAL:
[ ] G1: Model geometry coherent (no dislocated segments)
[ ] G2: All three views show same phase state (time consistency)
```

Total: 16 items (box task) / 7 items (stoop task, P1-P5 + G1-G2).
Pass threshold: all items checked. Any fail = stop, diagnose, re-generate motion.

### 5.5 Two-tier verification (mandatory)

1. **Tier 1 (Claude Code self-vision):** Read each PNG with the Read tool, evaluate
   checklist items, report per-item: OK / Warn / Fail.
2. **Tier 2 (user visual verification):** Request user to upload grid PNG to chat.
   User confirms or flags issues. Tier 2 is the binding decision gate.

Self-verification is early error detection. It does NOT replace user verification.
Moco analysis may NOT start until Tier 2 is confirmed.

### 5.6 GitHub push of grid PNGs

Grid PNGs are committed and pushed immediately after Tier 2 pass so the user can
inspect them via GitHub raw URL in any subsequent session without needing local access.

GitHub URL pattern:
```
https://raw.githubusercontent.com/parkch-meca/wearable-assist/main/
opensim_analysis/thoracolumbar_fb/docs/images/phase2_box/{filename}.png
```

---

## 6. Subtitle and Numeric Overlay (Burned-in)

### 6.1 Phase subtitle text (per task)

Subtitles are rendered as matplotlib text overlays composited onto each frame before
ffmpeg encoding. Font: DejaVu Sans (available in matplotlib), 14pt, white text,
semi-transparent dark background box.

**Box lift task (v11b baseline):**

| Time range | Subtitle text |
|---|---|
| t = 0.0 - 0.5 s | "Quiet standing — ES baseline (87.7% Suit OFF)" |
| t = 0.5 - 2.0 s | "Eccentric phase — trunk-first stoop, 20 kg box" |
| t = 2.0 - 2.5 s | "Grasp — peak lumbar load, hands at box sides" |
| t = 2.5 - 4.0 s | "Concentric phase — lift, box ascending" |
| t = 4.0 - 5.0 s | "Carry — trunk upright, ES partially active" |

**Stoop lift task (v5 baseline):**

| Time range | Subtitle text |
|---|---|
| t = 0.0 - 0.5 s | "Quiet standing — baseline" |
| t = 0.5 - 2.5 s | "Eccentric — lumbar flexion, knee nearly fixed" |
| t = 2.5 - 2.8 s | "Peak flexion — maximum ES recruitment" |
| t = 2.8 - 4.5 s | "Concentric — trunk extension" |
| t = 4.5 - 5.0 s | "Return to upright" |

### 6.2 Numeric overlay (suit comparison only)

Shown in the bottom panel at the right-hand side, updated every frame:

```
IL_R10_r:  {noload_val:.0f}%  |  {suit_val:.0f}%
ES mean:   {es_noload:.1f}%  |  {es_suit:.1f}%
Delta:     -{delta:.0f} %p   ({pct:.0f}% reduction)
```

The delta is color-coded: grey if < 10%, amber if 10-20%, green if > 20%.
This makes the suit effect immediately legible even without reading the numbers.

### 6.3 Timestamp display

Lower-left corner, always visible:
```
t = {current_time:.2f} s
```

---

## 7. Task-by-Task Video Plan

### 7.1 Stoop lift — Phase 1a re-render (priority 1)

**Status:** v5 motion verified, Moco result (24 N·m, MocoInverse) complete.
**Action:** Re-render suit comparison using 24 N·m condition (not 200 N·m).
**Script to update:** `render_v5_video.py` — add suit comparison panel using Phase 1a
suit solution.
**Output:** `stoop_v5_suit_comparison_{date}.mp4`
**Key numbers:** IL_R10_r 87.7% → 63.0%, ES mean -28%, slope 1.164 %/N·m, R² = 1.000

### 7.2 Box lift — v11b (priority 2)

**Status:** v11b motion 31/31 quantitative PASS, Stage 4 user-verified 8/8.
Moco Phase 2.C.4 v5 complete (4 conditions).
**Action:** Re-render suit comparison changing condition from B_suit200 to B_suit24
(interpolated from dose-response). Update annotation numbers.
**Script to update:** `render_box_v11b_suit_comparison.py` — change SOL_SUIT200 path
and annotation text.
**Output:** `box_v11b_suit_comparison_24Nm_{date}.mp4`
**Key numbers:** From Phase 2.C.4 v5, dose-response slope -0.129 %/N·m at grasp peak.

**Single-motion clean render (no comparison):**
`render_v11b_main_video.py` already produces 1920x720 side-by-side sagittal+3quarter.
Upgrade target resolution to 1920x1080 (add top margin or expand panels).

### 7.3 Squat lift (future — Step 3+)

**Prerequisite:** biomechanics-agent squat reference document (not yet created).
**Planned motion:** deep squat, knees past toes, lumbar relatively neutral.
**Key visual difference from box v11b:** larger knee flexion angle (~90°),
smaller lumbar contribution (~30° vs 55°).
**Layout:** identical template as box task.

### 7.4 Walk + carry (future — Step 3+)

**Prerequisite:** walking motion file with box in hands.
**Duration:** 5-10 s (one gait cycle + carry).
**Special consideration:** frame times for Stage 4 grid must be scaled to gait cycle
phases (heel strike, mid-stance, toe-off) rather than lift phases.

### 7.5 Patient transfer (future — Step 3+)

**Prerequisite:** biomechanics-agent patient transfer reference.
**Duration:** 10-15 s.
**Special consideration:** asymmetric loading, lateral bending component.
This task may require a 4th camera view (posterior) in Stage 4 grid.

---

## 8. Known Limitations (Carried Forward)

The following limitations from prior work must appear in any published video description
or supplementary material notes.

### 8.1 Kinematic-only foot contact (all tasks)

The motion files (.mot) use prescribed kinematics without ground contact constraints.
Foot positions are enforced by bisection-computed pelvis_tx/ty (v8+), but ground
reaction forces are not modeled kinematically. Visual rendering places the ground plane
at y = -0.905 m; any small residual mismatch (< 5 mm) is acceptable for visualization.

### 8.2 Suit effect representation

The SMA suit is modeled as a lumbar torque coupler (N·m). This is a first-order
approximation. Actual SMA fabric muscle behavior (force-velocity, temperature dependence,
hysteresis) is not captured. Dose-response results are valid for quasi-static stoop lifts
within the 0-24 N·m range.

### 8.3 Reserve actuator residuals

Phase 2.C.4 v5 solution has small reserve actuator contributions (< 8 N·m) at the pelvis.
This indicates a minor dynamic inconsistency in the prescribed kinematics that Moco corrects
with residual forces. The effect on ES activation is < 2 %p (confirmed by reserve sensitivity
analysis in `docs/reserve_sensitivity.md`). Absolute ES values should be interpreted with this
caveat; relative suit effects are robust (0.27 %p variation across reserve levels).

### 8.4 Single subject / single model

All results use ThoracolumbarFB v2.0 (male, ~1.75 m). Target population (65-year-old female
caregiving worker) requires anthropometric scaling and reduced ROM parameters per
`docs/biomech_reference/ground_box_lift_side_grip.md` Section 7.

---

## 9. Implementation Specification (for Step 2)

### 9.1 Rendering stack (confirmed working)

| Component | Role | Version / path |
|---|---|---|
| OpenSim Python API | FK, body positions, muscle geometry | `/home/sysop/miniconda3/envs/opensim/lib/python3.11/site-packages` |
| PyVista | Off-screen 3D rendering | `DISPLAY=:1` required |
| Matplotlib (Agg) | 2D overlay panels, grid composite | `matplotlib.use('Agg')` |
| Pillow (PIL) | Frame composite, resize | `Image`, `ImageDraw` |
| ffmpeg | Video encoding | system ffmpeg, h264/h265 |

### 9.2 Output directory structure

```
/data/opensim_results/
  video/
    {task}_{version}_{date}.mp4           <- primary output (not in git)
    {task}_v{N}_suit_comparison.mp4

/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/
  images/
    phase2_box/
      {motion}_stage4_grid.png            <- in git (verified)
      {motion}_stage4_t{X.X}_{view}.png  <- in git (verified)
    phase1a_stoop/
      {motion}_stage4_grid.png
    phase2_squat/  (future)
    phase2_walk/   (future)
    phase2_xfer/   (future)
  videos/
    {task}_{version}.mp4                 <- copy for git (< 50 MB, GitHub LFS if needed)

/tmp/{task}_frames/
  frame_{NNNN}.png                       <- temp, deleted after encode
```

### 9.3 Per-task config dict (template for Step 2 scripts)

```python
TASK_CONFIG = {
    'box_v11b': {
        'motion_file': '/data/stoop_motion/box_motion_v11b.mot',
        'box_traj':    '/data/stoop_motion/box_motion_v11b_box.sto',
        'model':       '/data/opensim_models/ThoracolumbarFB/.../MaleFullBodyModel_v2.0_OS4_modified_no_coupler_forearm_v1.osim',
        'sol_noload':  '/data/opensim_results/phase2c4_box_v11b/B_noload/solution.sto',
        'sol_suit':    None,  # interpolated from dose-response; no direct 24 N·m run yet
        'duration':    5.0,
        'frames':      [(0.0, 'Quiet Standing'), (1.5, 'Eccentric Mid'),
                        (2.0, 'Grasp / Peak'), (3.0, 'Concentric Mid'), (5.0, 'Carry')],
        'phases': {
            'Quiet':      (0.0, 0.5,  '#AAAAAA'),
            'Eccentric':  (0.5, 2.0,  '#1565C0'),
            'Grasp':      (2.0, 2.5,  '#CC2222'),
            'Concentric': (2.5, 4.0,  '#2E7D32'),
            'Carry':      (4.0, 5.0,  '#6A1B9A'),
        },
        'box_dims': {'W': 0.30, 'H': 0.30, 'D': 0.25},  # meters
        'key_numbers': {
            'il_r10_noload': 87.7,
            'il_r10_suit24': 63.0,
            'delta_pct':     28.0,
        },
        'subtitles': [
            (0.0, 0.5,  'Quiet standing — ES baseline'),
            (0.5, 2.0,  'Eccentric — trunk-first stoop, 20 kg box'),
            (2.0, 2.5,  'Grasp — peak lumbar load'),
            (2.5, 4.0,  'Concentric — lift, box ascending'),
            (4.0, 5.0,  'Carry — trunk upright'),
        ],
    },
    'stoop_v5': {
        'motion_file': '/data/stoop_motion/stoop_synthetic_v5.mot',
        'box_traj':    None,
        'model':       '/data/opensim_models/ThoracolumbarFB/.../MaleFullBodyModel_v2.0_OS4_modified.osim',
        'sol_noload':  '/data/stoop_results/stoop_v5/so_v5_StaticOptimization_activation.sto',
        'sol_suit':    None,  # Phase 1a MocoInverse suit result path TBD
        'duration':    5.0,
        'frames':      [(0.0, 'Quiet Standing'), (1.5, 'Eccentric Mid'),
                        (2.5, 'Peak Flexion'), (3.5, 'Concentric Mid'), (5.0, 'Upright')],
        'phases': {
            'Quiet':      (0.0, 0.5,  '#AAAAAA'),
            'Eccentric':  (0.5, 2.5,  '#1565C0'),
            'Peak':       (2.5, 2.8,  '#CC2222'),
            'Concentric': (2.8, 4.5,  '#2E7D32'),
            'Return':     (4.5, 5.0,  '#6A1B9A'),
        },
        'box_dims':    None,
        'key_numbers': {
            'il_r10_noload': 87.7,
            'il_r10_suit24': 63.0,
            'delta_pct':     28.0,
        },
        'subtitles': [
            (0.0, 0.5,  'Quiet standing'),
            (0.5, 2.5,  'Eccentric — lumbar flexion, knee nearly fixed'),
            (2.5, 2.8,  'Peak flexion — maximum ES recruitment'),
            (2.8, 4.5,  'Concentric — trunk extension'),
            (4.5, 5.0,  'Return to upright'),
        ],
    },
}
```

### 9.4 Skeleton vs mesh rendering decision

| Situation | Use | Reason |
|---|---|---|
| Stage 4 grid (quick) | Skeleton (cylinders + spheres) | Fast render < 30s, no geometry file needed |
| Main motion video | Full mesh (bone .vtp/.stl files) | Better visual quality for YouTube |
| Suit comparison video | Full mesh + ES muscle lines | Requires Moco solution for activation data |

Skeleton rendering is implemented in `render_v11b_stage4.py` (working).
Full mesh rendering is implemented in `render_v11b_main_video.py` and
`render_box_v11b_suit_comparison.py` (working).

### 9.5 ES muscle line rendering

ES prefixes (matched against muscle name, not path):
```python
ES_PREFIXES = ('IL_', 'LTpT_', 'LTpL_')
```

Activation source: Moco solution .sto file, column pattern `/forceset/{name}/activation`.
Line width: 5.0 px in video, 3.0 px in Stage 4 grid.
Colormap: custom linear (see Section 2.1), clim=[0.0, 1.0].

---

## 10. Integration with Other Step 1 Reports

This framework depends on or informs the following Step 1 architecture documents:

| Agent | Report | Dependency |
|---|---|---|
| opensim-agent (1.1) | Model infrastructure | Model paths and variants confirmed |
| biomechanics-agent (1.2) | Motion generation spec | Stage 4 frame times depend on task timeline |
| opensim-agent / moco-agent (1.3) | Suit module | Key numbers (28% reduction) confirmed here |
| viz-agent (this, 1.4) | Visualization framework | Provides layout spec to all agents |

When Step 2 implementation begins, the task config dict (Section 9.3) must be populated
with the final model paths and Moco solution paths confirmed by the other agents.

---

## 11. Checklist for Step 2 Readiness

Before any implementation script is written in Step 2, verify:

- [ ] V1: Final model path for no_coupler_forearm_v1 variant confirmed (opensim-agent 1.1)
- [ ] V2: Box v11b Stage 4 user verification: 8/8 confirmed (completed, see grid PNG)
- [ ] V3: Phase 2.C.4 v5 Moco solutions available for B_noload and at least one B_suit condition
- [ ] V4: Phase 1a suit Moco solution path confirmed (for stoop comparison video)
- [ ] V5: ffmpeg available on system (`which ffmpeg` returns valid path)
- [ ] V6: DISPLAY=:1 Xvfb running (`xdpyinfo -display :1` succeeds)
- [ ] V7: ES color schema reviewed by CHEOL HOON (Section 2.1)
- [ ] V8: Suit condition for comparison confirmed as 24 N·m (not 200 N·m)

Items V5, V6 are environment checks. Items V1-V4 depend on other agents' Step 1 outputs.
Items V7-V8 require user confirmation before comparison video is rendered.

---

_Document version: 1.0_
_Authors: viz-agent (Step 1.4 design), 2026-04-29_
_Next revision: after Step 2 implementation, record actual render times and file sizes_
