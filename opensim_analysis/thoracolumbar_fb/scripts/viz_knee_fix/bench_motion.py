"""[벤치 ■2] 들기 구간 운동학 생성 — 영상 ACTIVE 궤적을 모델 좌표로 변환.

■ 구간
  t = 3.0 ~ 5.8 s (30 fps · 85 프레임). 영상에서 몸통 경사 0° → +71°, 케틀벨이 바닥에서
  떠올라 직립까지 가는 **들기 구간**이다.

■ 프레임별 목표 (영상 실측)
  몸통 경사  어깨–고관절 선 (0° = 수평)
  대퇴 경사  벤치 패드가 고정 — 프레임별 실측값 그대로
  무릎 3° 고정 (벤치 구속), 팔은 매 프레임 수직으로 늘어뜨린다

■ 요추/골반 분담 (영상으로 분리 불가 → 두 변형)
  A 중립 요추 : 최저점 요추 굴곡 10°
  B 절반 분담 : 최저점 요추 굴곡 30°
  직립으로 갈수록 요추 굴곡은 선형으로 0 에 수렴시킨다 (φ(t) = φ_max · (1 − tilt/71))
"""
import os
import sys
import json
import numpy as np
import opensim as osim

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bench_posture as BP

OUT = '/data/suit_bench'
D2R = np.pi / 180
T0, T1 = 3.0, 5.8
TILT_TOP = 71.0
FEMUR_FIX = 122.5        # 최저점 실측 대퇴각 (벤치 패드 고정)


def video_targets():
    """영상 ACTIVE 패널에서 프레임별 (t, 몸통 경사, 대퇴 각)."""
    d = json.load(open(f'{OUT}/pose_raw.json'))
    rows = [r for r in d['res']['active'] if r and T0 - 1e-6 <= r['t'] <= T1 + 1e-6]
    out = []
    for r in rows:
        a = r['trunk'] if r['trunk'] > 0 else r['trunk'] + 360
        tilt = 180.0 - a                     # 0 = 수평, + = 신전
        out.append(dict(t=r['t'], tilt=tilt, thigh=r['thigh']))
    return out


def main():
    tg = video_targets()
    print(f'들기 구간 {tg[0]["t"]:.2f}~{tg[-1]["t"]:.2f} s · {len(tg)} 프레임 · '
          f'몸통 {tg[0]["tilt"]:+.1f}° → {tg[-1]["tilt"]:+.1f}°', flush=True)

    m = osim.Model(BP.MODEL)
    m.initSystem()
    cs = m.getCoordinateSet()
    coords = [cs.get(i).getName() for i in range(cs.getSize())]
    rot = {c: (cs.get(c).getMotionType() == 1) for c in coords}

    for key, phi_max in BP.VARIANTS.items():
        rows = []
        warm = None
        for r in tg:
            # 목표각을 모델 규약으로 (180 = 전방 수평)
            # 모델 규약: 180 = 전방 수평, 경사 tilt 만큼 들리면 180 − tilt
            BP.TARGET['trunk'] = 180.0 - r['tilt']
            # 대퇴는 벤치 패드가 잡고 있다 → 최저점 값으로 고정 (영상의 10° 드리프트는
            # 랜드마크 잡음으로 보고 쓰지 않는다)
            BP.TARGET['femur'] = FEMUR_FIX
            phi = phi_max * max(0.0, 1.0 - max(r['tilt'], 0.0) / TILT_TOP)
            s, pt, hf, res, arm = BP.solve_posture(m, phi, x0=warm)
            warm = np.array([pt, hf])
            vals = {c: 0.0 for c in coords}
            vals['pelvis_tilt'] = pt
            for nm, f in BP.LUMB:
                vals[nm] = -phi * f
            for sd in ('r', 'l'):
                vals[f'hip_flexion_{sd}'] = hf
                vals[f'knee_angle_{sd}'] = -3.0
                vals[f'elv_angle_{sd}'] = arm
            rows.append((r['t'], vals, phi, pt, hf, arm, res))
        mot = f'{OUT}/bench_{key}.mot'
        with open(mot, 'w') as f:
            f.write(f'bench_{key}\nversion=1\nnRows={len(rows)}\n'
                    f'nColumns={len(coords)+1}\ninDegrees=yes\n\n'
                    'Units are S.I. units (second, meters, Newtons, ...)\n\n'
                    'endheader\ntime\t' + '\t'.join(coords) + '\n')
            for t, vals, *_ in rows:
                f.write('\t'.join([f'{t:.6f}'] +
                                  [f'{vals[c]:.6f}' for c in coords]) + '\n')
        r0, rN = rows[0], rows[-1]
        print(f'  [{key}] φ {phi_max:.0f}° → 0°  ·  골반 {r0[3]:+.1f} → {rN[3]:+.1f}° · '
              f'고관절 {r0[4]:+.1f} → {rN[4]:+.1f}° · 어깨 {r0[5]:+.1f} → {rN[5]:+.1f}°',
              flush=True)
        print(f'          잔차 최대 {max(max(abs(x) for x in rr[6]) for rr in rows):.3f}° · '
              f'SAVED {mot}', flush=True)


if __name__ == '__main__':
    main()
