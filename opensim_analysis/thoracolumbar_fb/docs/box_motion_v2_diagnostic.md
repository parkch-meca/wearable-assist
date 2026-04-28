# Box Motion v2 — Quantitative Diagnostic

Source: `/data/stoop_motion/stoop_box20kg_v2.mot`

| Issue | Quantitative measurement |
|---|---|
| (i) Foot embedding | Max **15.2 cm** below render grid (y=-0.905) at t=2.00 s. Embedded > 1 cm during t=[1.15, 2.85] s (1.70 s out of 5) |
| (ii) Box vs hand at grasp | Static box top y=-0.755 m vs hand_center y=-0.606 m at t=2.0. Vertical gap = **+14.9 cm** (hand above box top). xz aligned (+0.0, +0.0) cm |
| (iii) Box pop at grasp | Box jumps **+14.9 cm vertical** in one frame at t=2.0 (+0.0 cm forward, +0.0 cm lateral) |
| (iv) Hand-box tracking after grasp | Hand vertical velocity max |v|=1.156 m/s during t=2.0–3.5. Renderer trajectory follows hand exactly (no decoupling). |

## Detailed numbers

### (i) Foot embedding profile

- calcn_r y range: [-1.057, -0.905] m
- Render grid y: -0.905 m
- Max embedding: 15.2 cm at t = 2.00 s (during peak bend)
- Duration with >1 cm embed: 1.70 s (mid-stoop)
- Cause: motion sets pelvis_ty=−0.32 m which drops the entire body; no ground contact constraint.

### (ii) Hand reach vs static box at grasp

- Hand center y at t=2.0: **-0.606 m**
- Static box top y in renderer: **-0.755 m**
- Vertical gap: **+14.9 cm** (hand sits this much above box top)
- Cause: the kinematic motion does not bend deep enough for hands to reach the box top at the static floor location.

### (iii) Renderer box pop at grasp

- Box center pre-grasp (t=1.99): [0.706, -0.83, -0.032]
- Box center post-grasp (t=2.00): [0.7063891589794763, -0.6812203682890773, -0.03160044328104493]
- Discontinuity: (+0.0, +14.9, +0.0) cm in one frame
- Cause: renderer switches box position from static (floor) to hand-following abruptly; no transition.

### (iv) Hand-box tracking continuity

- Hand-y velocity range during 2.0–3.5 s: [-0.000, 1.156] m/s
- Max |hand-y velocity| = 1.156 m/s
- Once grasp is engaged, the renderer keeps box exactly at hand_y - BOX_SIZE_Y/2; no decoupling artifact.

## Root-cause summary

| Root cause | Manifestation | Fix path |
|---|---|---|
| Motion has no ground contact constraint | Foot embedding (i) | A: ignore (kinematic-only); B: MocoTrack with foot constraint; C: regenerate motion |
| Motion does not bend deep enough | Hand-box gap at grasp (ii) | A: accept gap; B/C: regenerate with deeper bend |
| Renderer logic switches box at t=2.0 (no transition) | Box pop (iii) | A: smooth transition in renderer (no Moco needed); B/C: same |
| Renderer keeps box on hand after grasp | Tracking (iv) — actually fine | (no fix needed) |
