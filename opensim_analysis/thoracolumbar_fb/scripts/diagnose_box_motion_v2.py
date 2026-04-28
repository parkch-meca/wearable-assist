"""Part 2.0 — Quantitative diagnostic of stoop_box20kg_v2.mot.

Four hypothesized issues to quantify:
  (i)   Foot embedding below render grid (y = −0.905)
  (ii)  Box position vs hand center at grasp (t=2.0)
  (iii) Box "pop" at grasp (discontinuity at t=2.0)
  (iv)  Hand-box tracking after grasp (t=2.0–3.0 s)

Output: docs/box_motion_v2_diagnostic.md  (markdown table + figures)
"""
import os
os.environ.setdefault('OPENSIM_USE_VISUALIZER', '0')
from pathlib import Path
import numpy as np
import opensim as osim
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

MODEL_BASE = '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified.osim'
MOT = '/data/stoop_motion/stoop_box20kg_v2.mot'
OUT_DIR = Path('/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/phase2_box')
OUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT = Path('/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/box_motion_v2_diagnostic.md')

# Convention from previous render scripts:
GRID_Y = -0.905
BOX_BOTTOM_Y_RENDER = -0.83  # latest renderer setting (BOX_FLOOR_Y in render_box_comparison.py)
BOX_SIZE_Y = 0.15  # 15 cm box height
BOX_FLOOR_X = 0.706
BOX_FLOOR_Z = -0.032
BOX_HAND_X_OFFSET = 0.08
GRASP_T = 2.0


def main():
    print('=== Box motion v2 diagnostic ===')
    m = osim.Model(MODEL_BASE)
    state = m.initSystem()
    cs = m.getCoordinateSet()
    bs = m.getBodySet()

    tbl = osim.TimeSeriesTable(MOT)
    times = np.array(list(tbl.getIndependentColumn()))
    labels = list(tbl.getColumnLabels())
    print(f'Motion: {tbl.getNumRows()} rows × {tbl.getNumColumns()} cols, t=[{times[0]:.3f},{times[-1]:.3f}]')

    def apply_at(t):
        idx = int(np.argmin(np.abs(times - t)))
        row = tbl.getRowAtIndex(idx)
        for ci, name in enumerate(labels):
            if not cs.contains(name): continue
            v = row[ci]; c = cs.get(name)
            if c.getMotionType() == 1: v = np.radians(v)
            try: c.setValue(state, v, False)
            except Exception: pass
        m.assemble(state); m.realizePosition(state)

    def bp(name):
        g = bs.get(name).getPositionInGround(state)
        return np.array([g.get(0), g.get(1), g.get(2)])

    # Sample positions across t=0..5 in 0.05s steps
    sample_t = np.arange(0.0, 5.0 + 1e-9, 0.05)
    foot_R, foot_L = [], []
    hand_R, hand_L = [], []
    for t in sample_t:
        apply_at(t)
        foot_R.append(bp('calcn_r')); foot_L.append(bp('calcn_l'))
        hand_R.append(bp('hand_R'));  hand_L.append(bp('hand_L'))
    foot_R = np.array(foot_R); foot_L = np.array(foot_L)
    hand_R = np.array(hand_R); hand_L = np.array(hand_L)
    hand_C = (hand_R + hand_L) / 2.0

    # === (i) Foot embedding ===
    print('\n=== (i) Foot embedding (y vs grid y=−0.905) ===')
    foot_R_y = foot_R[:, 1]; foot_L_y = foot_L[:, 1]
    embed_R = GRID_Y - foot_R_y
    embed_R_max = embed_R.max(); embed_R_t = sample_t[int(embed_R.argmax())]
    print(f'  calcn_r y: range [{foot_R_y.min():.3f}, {foot_R_y.max():.3f}]')
    print(f'  Max embedding below grid = {embed_R_max*100:.1f} cm  (at t={embed_R_t:.2f})')
    # When does embedding start?
    first_embed_idx = np.where(embed_R > 0.01)[0]
    embed_start = sample_t[first_embed_idx[0]] if len(first_embed_idx) else None
    embed_end = sample_t[first_embed_idx[-1]] if len(first_embed_idx) else None
    print(f'  Embedded (>1cm below grid) during t=[{embed_start},{embed_end}]')

    # === (ii) Box vs hand at grasp (t=2.0) ===
    print('\n=== (ii) Box vs hand position at grasp t=2.0 ===')
    apply_at(2.0)
    hR2 = bp('hand_R'); hL2 = bp('hand_L'); hC2 = 0.5*(hR2+hL2)
    box_top_static = BOX_BOTTOM_Y_RENDER + BOX_SIZE_Y/2 + BOX_SIZE_Y/2  # = -0.83 + 0.075 + 0.075 = -0.68 (top)
    # Actually box center=BOX_FLOOR_Y in renderer; box top = center + BOX_SIZE_Y/2
    box_top_at_grasp = BOX_BOTTOM_Y_RENDER + BOX_SIZE_Y/2  # -0.83 + 0.075 = -0.755
    print(f'  hand_R at t=2.0: ({hR2[0]:+.3f}, {hR2[1]:+.3f}, {hR2[2]:+.3f})')
    print(f'  hand_L at t=2.0: ({hL2[0]:+.3f}, {hL2[1]:+.3f}, {hL2[2]:+.3f})')
    print(f'  hand_center  : ({hC2[0]:+.3f}, {hC2[1]:+.3f}, {hC2[2]:+.3f})')
    print(f'  Static box position (renderer): center=(0.706, -0.83, -0.032), top y={box_top_at_grasp:.3f}')
    gap_xz = ((hC2[0]+BOX_HAND_X_OFFSET) - 0.706, hC2[2] - BOX_FLOOR_Z)
    gap_y = hC2[1] - box_top_at_grasp
    print(f'  Gap (hand+offset vs box-top): xz=({gap_xz[0]*100:+.1f},{gap_xz[1]*100:+.1f}) cm, y={gap_y*100:+.1f} cm')

    # === (iii) Box pop at grasp ===
    print('\n=== (iii) Box pop at grasp (t=1.99 vs 2.00) ===')
    # Static box center: (0.706, -0.83, -0.032)
    # After grasp, render uses: box_center = (hand_x + 0.08, hand_y - BOX_SIZE_Y/2, hand_z)
    apply_at(1.99)
    hC_pre = 0.5*(bp('hand_R') + bp('hand_L'))
    box_pre = np.array([0.706, BOX_BOTTOM_Y_RENDER, BOX_FLOOR_Z])  # static
    apply_at(2.00)
    hC_post = 0.5*(bp('hand_R') + bp('hand_L'))
    box_post = np.array([hC_post[0]+BOX_HAND_X_OFFSET, hC_post[1]-BOX_SIZE_Y/2, hC_post[2]])
    pop = box_post - box_pre
    print(f'  Box center pre-grasp (t=1.99): ({box_pre[0]:+.3f}, {box_pre[1]:+.3f}, {box_pre[2]:+.3f})')
    print(f'  Box center post-grasp (t=2.00): ({box_post[0]:+.3f}, {box_post[1]:+.3f}, {box_post[2]:+.3f})')
    print(f'  POP = ({pop[0]*100:+.1f}, {pop[1]*100:+.1f}, {pop[2]*100:+.1f}) cm')

    # === (iv) Hand-box tracking after grasp (continuity) ===
    print('\n=== (iv) Hand-box tracking continuity (t=2.0..3.5) ===')
    # Compute hand_center vertical motion vs time after grasp
    mask_post = (sample_t >= 2.0) & (sample_t <= 3.5)
    # For each sample after grasp, the box should ideally be at hand_y - BOX_SIZE_Y/2
    # Velocity of hand_center.y
    t_post = sample_t[mask_post]
    hand_C_post = hand_C[mask_post]
    dt = np.diff(t_post).mean()
    vel_hand_y = np.gradient(hand_C_post[:, 1], dt)
    # Max vertical velocity = how fast box would have to move
    print(f'  Hand-y vertical velocity range: [{vel_hand_y.min():.3f}, {vel_hand_y.max():.3f}] m/s')
    print(f'  Max |vel| = {abs(vel_hand_y).max():.3f} m/s  → box must track this rate')
    # Discontinuity check at exact t=2.0 transition (jump from static to following)
    # Already covered in (iii)

    # === Plot ===
    fig, axs = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

    # Foot y vs grid
    ax = axs[0]
    ax.plot(sample_t, foot_R_y, lw=2, color='tab:red', label='calcn_r y')
    ax.plot(sample_t, foot_L_y, lw=2, color='tab:blue', label='calcn_l y', linestyle='--')
    ax.axhline(GRID_Y, color='k', ls=':', lw=1.5, label=f'render grid y={GRID_Y}')
    ax.fill_between(sample_t, GRID_Y, np.minimum(foot_R_y, GRID_Y),
                     where=(foot_R_y < GRID_Y - 0.001),
                     color='red', alpha=0.2, label='embedded')
    ax.set_ylabel('y (m)')
    ax.set_title(f'(i) Foot embedding — max {embed_R_max*100:.1f} cm below grid at t={embed_R_t:.1f} s',
                 loc='left', fontsize=11, fontweight='bold')
    ax.legend(loc='lower right'); ax.grid(True, alpha=0.3)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)

    # Hand y vs box position (renderer's box trajectory)
    ax = axs[1]
    ax.plot(sample_t, hand_C[:, 1], lw=2, color='tab:purple', label='hand_center y')
    # Renderer box trajectory
    box_y = np.full_like(sample_t, BOX_BOTTOM_Y_RENDER)
    box_y[sample_t >= GRASP_T] = hand_C[sample_t >= GRASP_T, 1] - BOX_SIZE_Y/2
    ax.plot(sample_t, box_y, lw=2, color='tab:brown', label='box center y (renderer)', linestyle='-')
    ax.plot(sample_t, box_y + BOX_SIZE_Y/2, lw=1, color='tab:brown', alpha=0.5, label='box top y')
    ax.axvline(GRASP_T, color='k', ls=':', lw=1, alpha=0.5)
    ax.set_ylabel('y (m)')
    ax.set_title(f'(ii)+(iii) Box vs hand — pop at t=2.0: ({pop[0]*100:+.1f}, {pop[1]*100:+.1f}, {pop[2]*100:+.1f}) cm',
                 loc='left', fontsize=11, fontweight='bold')
    ax.legend(loc='lower right'); ax.grid(True, alpha=0.3)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)

    # Hand vertical velocity
    ax = axs[2]
    full_dt = np.diff(sample_t).mean()
    vel_full = np.gradient(hand_C[:, 1], full_dt)
    ax.plot(sample_t, vel_full, lw=1.5, color='tab:green', label='hand_y velocity (m/s)')
    ax.axvline(GRASP_T, color='k', ls=':', lw=1, alpha=0.5)
    ax.axhline(0, color='k', lw=0.5)
    ax.set_xlabel('time (s)'); ax.set_ylabel('velocity (m/s)')
    ax.set_title(f'(iv) Hand vertical velocity — max |vel|={abs(vel_full).max():.2f} m/s',
                 loc='left', fontsize=11, fontweight='bold')
    ax.legend(loc='lower right'); ax.grid(True, alpha=0.3)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)

    fig.tight_layout()
    fig.savefig(OUT_DIR / 'box_motion_v2_diagnostic.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'\nSaved {OUT_DIR / "box_motion_v2_diagnostic.png"}')

    # ===== Markdown report =====
    with open(REPORT, 'w') as f:
        f.write('# Box Motion v2 — Quantitative Diagnostic\n\n')
        f.write(f'Source: `{MOT}`\n\n')
        f.write('| Issue | Quantitative measurement |\n|---|---|\n')
        f.write(f'| (i) Foot embedding | Max **{embed_R_max*100:.1f} cm** below render grid (y={GRID_Y}) at t={embed_R_t:.2f} s. '
                f'Embedded > 1 cm during t=[{embed_start:.2f}, {embed_end:.2f}] s ({(embed_end-embed_start):.2f} s out of 5) |\n')
        f.write(f'| (ii) Box vs hand at grasp | Static box top y={box_top_at_grasp:.3f} m vs hand_center y={hC2[1]:+.3f} m at t=2.0. '
                f'Vertical gap = **{gap_y*100:+.1f} cm** (hand above box top). xz aligned ({gap_xz[0]*100:+.1f}, {gap_xz[1]*100:+.1f}) cm |\n')
        f.write(f'| (iii) Box pop at grasp | Box jumps **{pop[1]*100:+.1f} cm vertical** in one frame at t=2.0 '
                f'({pop[0]*100:+.1f} cm forward, {pop[2]*100:+.1f} cm lateral) |\n')
        f.write(f'| (iv) Hand-box tracking after grasp | Hand vertical velocity max |v|={abs(vel_hand_y).max():.3f} m/s during t=2.0–3.5. '
                f'Renderer trajectory follows hand exactly (no decoupling). |\n\n')

        f.write('## Detailed numbers\n\n')
        f.write('### (i) Foot embedding profile\n\n')
        f.write(f'- calcn_r y range: [{foot_R_y.min():.3f}, {foot_R_y.max():.3f}] m\n')
        f.write(f'- Render grid y: {GRID_Y:.3f} m\n')
        f.write(f'- Max embedding: {embed_R_max*100:.1f} cm at t = {embed_R_t:.2f} s (during peak bend)\n')
        f.write(f'- Duration with >1 cm embed: {(embed_end-embed_start):.2f} s (mid-stoop)\n')
        f.write('- Cause: motion sets pelvis_ty=−0.32 m which drops the entire body; no ground contact constraint.\n\n')

        f.write('### (ii) Hand reach vs static box at grasp\n\n')
        f.write(f'- Hand center y at t=2.0: **{hC2[1]:+.3f} m**\n')
        f.write(f'- Static box top y in renderer: **{box_top_at_grasp:.3f} m**\n')
        f.write(f'- Vertical gap: **{gap_y*100:+.1f} cm** (hand sits this much above box top)\n')
        f.write('- Cause: the kinematic motion does not bend deep enough for hands to reach the box top at the static floor location.\n\n')

        f.write('### (iii) Renderer box pop at grasp\n\n')
        f.write(f'- Box center pre-grasp (t=1.99): {box_pre.tolist()}\n')
        f.write(f'- Box center post-grasp (t=2.00): {box_post.tolist()}\n')
        f.write(f'- Discontinuity: ({pop[0]*100:+.1f}, {pop[1]*100:+.1f}, {pop[2]*100:+.1f}) cm in one frame\n')
        f.write('- Cause: renderer switches box position from static (floor) to hand-following abruptly; no transition.\n\n')

        f.write('### (iv) Hand-box tracking continuity\n\n')
        f.write(f'- Hand-y velocity range during 2.0–3.5 s: [{vel_hand_y.min():.3f}, {vel_hand_y.max():.3f}] m/s\n')
        f.write(f'- Max |hand-y velocity| = {abs(vel_hand_y).max():.3f} m/s\n')
        f.write('- Once grasp is engaged, the renderer keeps box exactly at hand_y - BOX_SIZE_Y/2; no decoupling artifact.\n\n')

        f.write('## Root-cause summary\n\n')
        f.write('| Root cause | Manifestation | Fix path |\n|---|---|---|\n')
        f.write('| Motion has no ground contact constraint | Foot embedding (i) | A: ignore (kinematic-only); B: MocoTrack with foot constraint; C: regenerate motion |\n')
        f.write('| Motion does not bend deep enough | Hand-box gap at grasp (ii) | A: accept gap; B/C: regenerate with deeper bend |\n')
        f.write('| Renderer logic switches box at t=2.0 (no transition) | Box pop (iii) | A: smooth transition in renderer (no Moco needed); B/C: same |\n')
        f.write('| Renderer keeps box on hand after grasp | Tracking (iv) — actually fine | (no fix needed) |\n')


if __name__ == '__main__':
    main()
