"""Step 1.5.1 — kinematic verification of stoop_synthetic_v5.mot.

Goal: determine whether the IL_R10 double-peak in MocoInverse output
(t≈2.3 s, t≈3.1 s with dip at t≈2.7 s) reflects (A) faithful tracking of a
motion plateau, (B) genuine phasic activation strategy, or (C) a mixed
case. Output Case label + supporting plots.
"""
import os
os.environ.setdefault('OPENSIM_USE_VISUALIZER', '0')
from pathlib import Path
import numpy as np
import opensim as osim
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

MOT = '/data/stoop_motion/stoop_synthetic_v5.mot'
OUT = Path('/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/phase1a_full')
OUT.mkdir(parents=True, exist_ok=True)

KEY_COORDS = ['L5_S1_FE','L4_L5_FE','L3_L4_FE','L2_L3_FE','L1_L2_FE','T12_L1_FE',
              'hip_flexion_r','hip_flexion_l','knee_angle_r','knee_angle_l','pelvis_tilt']


def load(name):
    tbl = osim.TimeSeriesTable(MOT)
    times = np.array(list(tbl.getIndependentColumn()))
    labels = list(tbl.getColumnLabels())
    if name not in labels:
        return None, None
    j = labels.index(name)
    n = tbl.getNumRows()
    out = np.zeros(n)
    for i in range(n):
        out[i] = tbl.getRowAtIndex(i)[j]
    return times, out


def main():
    # Load coords (file is in degrees)
    data = {}
    for c in KEY_COORDS:
        t, v = load(c)
        if v is not None:
            data[c] = (t, v)
    print(f'Loaded {len(data)} coords')

    # Pick representative coords for the figure
    sagittal = ['L5_S1_FE','L3_L4_FE','T12_L1_FE','hip_flexion_r','knee_angle_r','pelvis_tilt']
    sagittal = [c for c in sagittal if c in data]

    # Compute aggregate "lumbar flexion" = sum of all FE coords (degrees)
    fe_coords = [c for c in KEY_COORDS if c.endswith('_FE') and c in data]
    if fe_coords:
        t_ref = data[fe_coords[0]][0]
        lumbar_total = np.zeros_like(t_ref)
        for c in fe_coords:
            lumbar_total += data[c][1]
        # store under a synthetic key
        data['__lumbar_FE_sum'] = (t_ref, lumbar_total)

    # Velocity (deg/s) of lumbar_total via central diff
    t_ref = data['__lumbar_FE_sum'][0]
    dt = np.diff(t_ref).mean()
    lumbar_total = data['__lumbar_FE_sum'][1]
    velocity = np.gradient(lumbar_total, dt)

    # ---- Plot 1: full 0-5s ----
    fig, axs = plt.subplots(3, 1, figsize=(12, 9), sharex=True)
    ax = axs[0]
    for c in sagittal:
        ax.plot(data[c][0], data[c][1], lw=1.5, label=c)
    # phase shading
    for ts, te, color, name in [(0,1,'#888888','Q'),(1,2,'#1f77b4','Ecc'),
                                 (2,2.5,'#d62728','Hold'),(2.5,4,'#2ca02c','Con'),
                                 (4,5,'#ff7f0e','Rec')]:
        ax.axvspan(ts, te, alpha=0.10, color=color)
    ax.set_ylabel('coord value (deg or m)')
    ax.set_title('Reference motion stoop_synthetic_v5.mot — sagittal coordinates (full 0–5 s)')
    ax.legend(fontsize=8, ncol=2, loc='upper right')
    ax.grid(True, alpha=0.3); ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)

    ax = axs[1]
    ax.plot(t_ref, lumbar_total, lw=2, color='#d62728', label='Σ Lumbar FE (T12-L5_S1)')
    for ts, te, color, name in [(0,1,'#888888','Q'),(1,2,'#1f77b4','Ecc'),
                                 (2,2.5,'#d62728','Hold'),(2.5,4,'#2ca02c','Con'),
                                 (4,5,'#ff7f0e','Rec')]:
        ax.axvspan(ts, te, alpha=0.10, color=color)
    ax.set_ylabel('aggregate lumbar flexion (deg)')
    ax.legend(loc='upper right'); ax.grid(True, alpha=0.3)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)

    ax = axs[2]
    ax.plot(t_ref, velocity, lw=2, color='#1f77b4', label='d(Σ Lumbar FE)/dt')
    ax.axhline(0, color='k', lw=0.5)
    for ts, te, color, name in [(0,1,'#888888','Q'),(1,2,'#1f77b4','Ecc'),
                                 (2,2.5,'#d62728','Hold'),(2.5,4,'#2ca02c','Con'),
                                 (4,5,'#ff7f0e','Rec')]:
        ax.axvspan(ts, te, alpha=0.10, color=color)
    ax.set_ylabel('angular velocity (deg/s)')
    ax.set_xlabel('time (s)')
    ax.legend(loc='upper right'); ax.grid(True, alpha=0.3)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)

    fig.tight_layout()
    fig.savefig(OUT / 'motion_kinematics_full.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'Saved motion_kinematics_full.png')

    # ---- Plot 2: zoom to 2.0-3.5s (dip region) ----
    mask = (t_ref >= 1.8) & (t_ref <= 3.5)
    fig, axs = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    ax = axs[0]
    ax.plot(t_ref[mask], lumbar_total[mask], lw=2, color='#d62728', label='Σ Lumbar FE')
    for ts, te, color in [(2,2.5,'#d62728'),(2.5,3.0,'#2ca02c')]:
        ax.axvspan(ts, te, alpha=0.12, color=color)
    ax.axvline(2.3, color='k', ls=':', lw=1, alpha=0.5)
    ax.axvline(2.7, color='k', ls=':', lw=1, alpha=0.5)
    ax.axvline(3.1, color='k', ls=':', lw=1, alpha=0.5)
    ax.text(2.3, lumbar_total[mask].max()*0.95, 't=2.3 (peak1?)', fontsize=8, ha='center')
    ax.text(2.7, lumbar_total[mask].max()*0.95, 't=2.7 (dip?)', fontsize=8, ha='center')
    ax.text(3.1, lumbar_total[mask].max()*0.95, 't=3.1 (peak2?)', fontsize=8, ha='center')
    ax.set_ylabel('aggregate lumbar flexion (deg)')
    ax.set_title('Zoom: t=1.8–3.5 s — does motion plateau at expected dip?')
    ax.legend(); ax.grid(True, alpha=0.3)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)

    ax = axs[1]
    ax.plot(t_ref[mask], velocity[mask], lw=2, color='#1f77b4', label='velocity')
    ax.axhline(0, color='k', lw=0.5)
    for ts, te, color in [(2,2.5,'#d62728'),(2.5,3.0,'#2ca02c')]:
        ax.axvspan(ts, te, alpha=0.12, color=color)
    ax.axvline(2.3, color='k', ls=':', lw=1, alpha=0.5)
    ax.axvline(2.7, color='k', ls=':', lw=1, alpha=0.5)
    ax.axvline(3.1, color='k', ls=':', lw=1, alpha=0.5)
    ax.set_ylabel('angular velocity (deg/s)')
    ax.set_xlabel('time (s)')
    ax.legend(); ax.grid(True, alpha=0.3)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / 'motion_kinematics_dip_zoom.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'Saved motion_kinematics_dip_zoom.png')

    # ---- Velocity-only stand-alone plot ----
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(t_ref, velocity, lw=2, color='#1f77b4', label='Σ Lumbar FE velocity (deg/s)')
    ax.axhline(0, color='k', lw=0.5)
    for ts, te, color, name in [(0,1,'#888888','Q'),(1,2,'#1f77b4','Ecc'),
                                 (2,2.5,'#d62728','Hold'),(2.5,4,'#2ca02c','Con'),
                                 (4,5,'#ff7f0e','Rec')]:
        ax.axvspan(ts, te, alpha=0.10, color=color)
        ax.text((ts+te)/2, ax.get_ylim()[1]*0.92 if ax.get_ylim()[1]>0 else 50,
                name, ha='center', fontsize=9, fontweight='bold', color='#333')
    ax.set_xlabel('time (s)'); ax.set_ylabel('lumbar FE angular velocity (deg/s)')
    ax.set_title('Lumbar FE velocity — Hold phase plateau check')
    ax.legend(); ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / 'motion_velocity.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'Saved motion_velocity.png')

    # ---- Numeric Case judgment ----
    # Sample key time-points
    def at(t):
        i = int(np.argmin(np.abs(t_ref - t)))
        return float(lumbar_total[i]), float(velocity[i])

    print('\n=== Lumbar FE (deg) and velocity (deg/s) at key times ===')
    print(f'{"t":>5} {"flex(deg)":>10} {"vel(deg/s)":>12}')
    for tk in [0.0, 1.0, 1.5, 2.0, 2.3, 2.5, 2.7, 3.0, 3.1, 3.5, 4.0, 5.0]:
        v, vel = at(tk)
        print(f'{tk:>5.2f} {v:>10.2f} {vel:>12.3f}')

    # Hold phase plateau test: max |velocity| over t=[2.0, 2.5]
    mask_hold = (t_ref >= 2.0) & (t_ref <= 2.5)
    max_vel_hold = float(np.abs(velocity[mask_hold]).max())
    mean_vel_hold = float(np.abs(velocity[mask_hold]).mean())
    # Same for early Concentric (2.5-3.0)
    mask_econ = (t_ref >= 2.5) & (t_ref <= 3.0)
    max_vel_econ = float(np.abs(velocity[mask_econ]).max())
    # Eccentric peak velocity
    mask_ecc = (t_ref >= 1.0) & (t_ref <= 2.0)
    max_vel_ecc = float(np.abs(velocity[mask_ecc]).max())

    print(f'\nMax |velocity| during phases (deg/s):')
    print(f'  Eccentric    : {max_vel_ecc:.2f}')
    print(f'  Hold         : {max_vel_hold:.2f}')
    print(f'  early Conc.  : {max_vel_econ:.2f}')
    print(f'\nHold mean |velocity| / Eccentric peak = {mean_vel_hold / max_vel_ecc:.3f}')

    if mean_vel_hold < 0.1 * max_vel_ecc:
        case = 'A'
        case_desc = 'Motion has clear plateau — Hold phase is near-static (vel < 10% of peak)'
    elif mean_vel_hold > 0.5 * max_vel_ecc:
        case = 'B'
        case_desc = 'Motion is monotonic — Hold velocity not particularly low; ES double peak likely reflects activation dynamics'
    else:
        case = 'C'
        case_desc = 'Mixed — partial plateau plus dynamics likely both contribute'

    print(f'\n*** CASE {case}: {case_desc} ***')
    print(f'    mean |vel|_Hold = {mean_vel_hold:.2f},  peak |vel|_Ecc = {max_vel_ecc:.2f}')
    print(f'    ratio Hold/Ecc  = {mean_vel_hold/max_vel_ecc*100:.1f}%')


if __name__ == '__main__':
    main()
