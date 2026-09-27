"""[벤치 ■2·■3] 장력 역산 분석 — 필요 T, 모멘트 암, 판정.

■ 목표
  G1  23 kg 에서 표면 ES 활성도 −40 % (들기 구간 평균 / 최저점 구간 병기)
  G2  근력 축소 모델 36 kg 에서 OFF 불가 → 가열 가능 (reserve 임계 2/5/10 N·m)

■ 지표
  표면 ES = L1~L3 높이대 후방 50 % (analyze_vest_so.surface_es, 38 근육) — 이전 보고와 동일
  reserve = (고관절 + 척추 *_FE) 최대 |M|
"""
import os
import sys
import json
import numpy as np
import opensim as osim

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze_vest_so as AV
import bench_posture as BP
import suit_vest_geom as VG

OUT = '/data/suit_bench'
SO = f'{OUT}/so'
TENS = [50.0, 100.0, 200.0, 300.0, 400.0, 600.0]
VARIANTS = ['A_neutral', 'B_half']
THRESH = (2.0, 5.0, 10.0)
NBOT = 12


def cond_dir(model_tag, variant, kb, cond):
    return f'{SO}/{model_tag}_{variant}_{kb:g}kg_{cond}'


def act_mean(d, cols, mask_n=None):
    t = osim.TimeSeriesTable(f'{d}/so_StaticOptimization_activation.sto')
    have = [c for c in cols if c in list(t.getColumnLabels())]
    A = np.vstack([[float(t.getDependentColumn(c)[i]) for i in range(t.getNumRows())]
                   for c in have]) * 100
    if mask_n:
        A = A[:, :mask_n]
    return float(A.mean()), float(A.max(axis=0).mean())


def reserves(d):
    t = osim.TimeSeriesTable(f'{d}/so_StaticOptimization_force.sto')
    hip = spine = 0.0
    for c in t.getColumnLabels():
        if not c.startswith('reserve_'):
            continue
        b = c[len('reserve_'):]
        if b.startswith('hip_flexion') or '_FE' in b:
            v = max(abs(float(t.getDependentColumn(c)[i]))
                    for i in range(t.getNumRows()))
            if b.startswith('hip'):
                hip = max(hip, v)
            else:
                spine = max(spine, v)
    return hip, spine


def moment_arms():
    """벤치 최저점에서 슈트 경로의 L5–S1 · 고관절 모멘트 암 (■3)."""
    m0 = osim.Model(BP.MODEL)
    m0.initSystem()
    s0 = VG.neutral(m0)
    P = {sd: VG.vest_waist_points(m0, s0, sd) for sd in ('R', 'L')}
    m = osim.Model(BP.MODEL)
    m.initSystem()
    bs = m.getBodySet()
    for sd, pts in P.items():
        pa = osim.PathActuator()
        pa.setName(f'vest_{sd}')
        pa.setOptimalForce(100.0)
        for i, (b, v) in enumerate(pts):
            pa.addNewPathPoint(f'vest_{sd}_p{i}', bs.get(b), osim.Vec3(*v))
        m.addForce(pa)
    m.finalizeConnections()
    m.initSystem()
    R = json.load(open(f'{OUT}/posture.json'))
    out = {}
    for key in VARIANTS:
        v = R[key]
        s = BP.set_pose(m, v['phi'], v['pelvis_tilt'], v['hip_flex'], arm=v['arm'])
        pa = osim.PathActuator.safeDownCast(m.getForceSet().get('vest_R'))
        row = {}
        for c in ('L5_S1_FE', 'L4_L5_FE', 'L3_L4_FE', 'L1_L2_FE', 'T12_L1_FE',
                  'T8_T9_FE', 'hip_flexion_r'):
            try:
                row[c] = pa.getGeometryPath().computeMomentArm(
                    s, m.getCoordinateSet().get(c)) * 1000
            except Exception:
                pass
        out[key] = row
    return out


def main():
    surf = AV.surface_es()
    rep = {'surf_n': len(surf), 'thresh': THRESH}

    print('=' * 104)
    print('[■3] 벤치 최저점 슈트 모멘트 암 (한쪽 경로, mm)')
    print('=' * 104)
    ma = moment_arms()
    rep['moment_arm'] = ma
    cols = list(next(iter(ma.values())).keys())
    print(f"  {'변형':12s}" + ''.join(f'{c:>12s}' for c in cols))
    for k, row in ma.items():
        print(f'  {k:12s}' + ''.join(f'{row[c]:12.1f}' for c in cols))

    print('\n' + '=' * 104)
    print('[G1] 23 kg — 장력별 표면 ES 활성도 변화 (목표 −40 %)')
    print('=' * 104)
    g1 = {}
    for v in VARIANTS:
        base = cond_dir('model_tight', v, 23, 'off')
        if not os.path.exists(f'{base}/so_StaticOptimization_activation.sto'):
            print(f'  [{v}] OFF 결과 없음')
            continue
        b_all, b_pk = act_mean(base, surf)
        b_bot, b_bpk = act_mean(base, surf, NBOT)
        g1[v] = dict(off=dict(all=b_all, bot=b_bot, all_pk=b_pk, bot_pk=b_bpk), T={})
        print(f'\n  [{v}] OFF 절대값: 들기 구간 평균 {b_all:.2f} % · 최저점 {b_bot:.2f} %')
        print(f"      {'T (한쪽/양측)':>16s} {'들기 구간':>12s} {'최저점':>12s} "
              f"{'고관절 res':>11s} {'척추 res':>10s}")
        for T in TENS:
            d = cond_dir('model_tight', v, 23, f'T{T:g}')
            if not os.path.exists(f'{d}/so_StaticOptimization_activation.sto'):
                continue
            a, _ = act_mean(d, surf)
            bo, _ = act_mean(d, surf, NBOT)
            hip, sp = reserves(d)
            ra = 100 * (a - b_all) / b_all
            rb = 100 * (bo - b_bot) / b_bot
            g1[v]['T'][T] = dict(all=a, bot=bo, rel_all=ra, rel_bot=rb,
                                 hip_res=hip, spine_res=sp)
            print(f'      {T:7.0f}/{2*T:<8.0f} {ra:+11.1f} % {rb:+11.1f} % '
                  f'{hip:11.2f} {sp:10.2f}')
        # −40 % 도달 T 보간
        for wk, lab in (('rel_all', '들기 구간'), ('rel_bot', '최저점')):
            xs = [T for T in TENS if T in g1[v]['T']]
            ys = [g1[v]['T'][T][wk] for T in xs]
            need = None
            for i in range(len(xs) - 1):
                if ys[i] > -40 >= ys[i + 1]:
                    f = (-40 - ys[i]) / (ys[i + 1] - ys[i])
                    need = xs[i] + f * (xs[i + 1] - xs[i])
                    break
            if need is None and ys and ys[-1] > -40:
                sl = (ys[-1] - ys[0]) / (xs[-1] - xs[0])
                need = xs[-1] + (-40 - ys[-1]) / sl if sl < 0 else None
                tagx = ' (외삽)'
            else:
                tagx = ''
            g1[v][f'need_{wk}'] = need
            print(f'      → {lab} −40 % 도달 T = '
                  f'{f"{need:.0f} N (한쪽) / {2*need:.0f} N (양측 합)" if need else "미도달"}{tagx}')
    rep['G1'] = g1

    print('\n' + '=' * 104)
    print('[G2] 36 kg 근력 축소 모델 — OFF 불가 → 가열 가능 인가')
    print('=' * 104)
    g2 = {}
    scaled = [d for d in os.listdir(SO) if d.startswith('model_s')]
    mtag = None
    for d in scaled:
        if '_36kg_off' in d:
            mtag = d.split('_')[0] + '_' + d.split('_')[1]
            break
    if mtag is None:
        print('  근력 축소 모델 결과 없음 (아직 미실행)')
    else:
        for v in VARIANTS:
            base = cond_dir(mtag, v, 36, 'off')
            if not os.path.exists(f'{base}/so_StaticOptimization_force.sto'):
                continue
            hip0, sp0 = reserves(base)
            g2[v] = dict(off=dict(hip=hip0, spine=sp0), T={})
            print(f"\n  [{v}] OFF: 고관절 {hip0:.2f} · 척추 {sp0:.2f} N·m  "
                  + ' '.join(f'{t:.0f}:{"가능" if max(hip0,sp0)<=t else "불가"}'
                             for t in THRESH))
            for T in TENS:
                d = cond_dir(mtag, v, 36, f'T{T:g}')
                if not os.path.exists(f'{d}/so_StaticOptimization_force.sto'):
                    continue
                hip, sp = reserves(d)
                w = max(hip, sp)
                g2[v]['T'][T] = dict(hip=hip, spine=sp, worst=w)
                print(f'      T {T:5.0f} N (한쪽) / {2*T:5.0f} N (양측): '
                      f'고관절 {hip:6.2f} · 척추 {sp:6.2f} → '
                      + ' '.join(f'{t:.0f}:{"가능" if w<=t else "불가"}' for t in THRESH))
    rep['G2'] = g2
    json.dump(rep, open(f'{OUT}/bench_metrics.json', 'w'), ensure_ascii=False,
              indent=1, default=float)
    print(f'\nSAVED {OUT}/bench_metrics.json')


if __name__ == '__main__':
    main()
