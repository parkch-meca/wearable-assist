"""[정정 2] 힘 모델 재구성 — 구동부(SMA) + 사슬(피부·끈·밴드) 직렬, 100 N 일괄 상한 제거.

■ 왜 바꾸나
  기존 solve() 는 가열·미가열 분기가 **모두 100 N 에서 잘려**, 수동/능동 차이도
  사슬 강성 효과도 표현하지 못했다 (스툽 허리는 사실상 항상 상한).

■ 구동부 (근육옷감, 구동부 길이 200 mm · 스트로크 60 mm = 30 %)
  미가열 : L_stand → 200 mm 구간을 평탄 응력 F_plat 로 신장. 200 mm 에서 메쉬 리미터(강체).
           ⇒ 착용 직립의 장력 = F_plat (그 이상이면 더 늘어나 버리므로)
  가열   : 구속 가열 힘 F_hot 에서 시작해 수축할수록 선형 감소, 140 mm 에서 0
           F_act(L) = F_hot · (L − 140)/(200 − 140),  0 ≤ F ≤ F_hot

■ 사슬 (구동부와 직렬: 피부 눌림 · 어깨끈 미끄러짐 · 허벅지 밴드 상승)
  linear    F = k·x
  bilinear  x ≤ x_k 는 k1, 그 이후 k2   (연질→경질 / 경질→연질 둘 다 표현 가능)

■ 평형
  경로 신장 ΔL 에 대해  (L_act − L_stand) + (x − x0) = ΔL,  F_act(L_act) = F_chain(x)
  x0 는 착용 직립(미가열) 상태의 사슬 변형 = x(F_plat)

⚠️ 어느 조합도 관찰을 만족하지 못하면 억지로 맞추지 않는다 (사용자 지시).
"""
import os
import sys
import json
import itertools
import numpy as np

L_MESH = 200.0          # mm — 메쉬 리미터 (구동부 최대 길이)
L_FREE = 140.0          # mm — 60 ℃ 완전 수축 길이 (수축률 30 %)
OUT = '/data/suit_vest'

# ── 사슬 ───────────────────────────────────────────────────────────
class Chain:
    def __init__(self, kind, **p):
        self.kind, self.p = kind, p

    def F(self, x):
        x = max(0.0, x)
        if self.kind == 'lin':
            return self.p['k'] * x
        k1, xk, k2 = self.p['k1'], self.p['xk'], self.p['k2']
        return k1 * x if x <= xk else k1 * xk + k2 * (x - xk)

    def x(self, F):
        F = max(0.0, F)
        if self.kind == 'lin':
            return F / self.p['k']
        k1, xk, k2 = self.p['k1'], self.p['xk'], self.p['k2']
        Fk = k1 * xk
        return F / k1 if F <= Fk else xk + (F - Fk) / k2

    def label(self):
        if self.kind == 'lin':
            return f"선형 k={self.p['k']:g}"
        return (f"이중 k1={self.p['k1']:g}/x{self.p['xk']:g}/k2={self.p['k2']:g}")


# ── 구동부 ─────────────────────────────────────────────────────────
def f_hot(L, F_hot):
    return float(np.clip(F_hot * (L - L_FREE) / (L_MESH - L_FREE), 0.0, F_hot))


def solve(dL, prm, heated):
    """경로 신장 dL(mm) 에서의 평형. 반환 dict."""
    L_stand, F_plat, F_hot_, ch = (prm['L_stand'], prm['F_plat'], prm['F_hot'],
                                   prm['chain'])
    x0 = ch.x(F_plat)
    if not heated:
        room = L_MESH - L_stand                     # 구동부가 늘어날 수 있는 여유
        if dL <= room:                              # 평탄 구간에서 전부 흡수
            return dict(F=F_plat, L_act=L_stand + dL, x=x0, act=dL, chain=0.0,
                        state='구동부 신장(평탄)')
        L_act = L_MESH
        x = x0 + (dL - room)
        return dict(F=ch.F(x), L_act=L_act, x=x, act=room, chain=dL - room,
                    state='메쉬 리미터 → 사슬이 나머지 흡수')
    # 가열 — L_act 에 대해 단조 → 이분법
    lo, hi = L_FREE, L_MESH

    def g(L):
        x = x0 + dL - (L - L_stand)
        return f_hot(L, F_hot_) - ch.F(max(0.0, x))
    if g(hi) <= 0:
        # 구동부를 최대(200 mm)로 늘려도 사슬이 더 세다 → 메쉬 리미터가 하중을 받는다.
        # 이때 장력은 가열력이 아니라 **사슬 변형**이 정한다 (미가열 분기와 같은 상황).
        x = max(0.0, x0 + dL - (hi - L_stand))
        return dict(F=ch.F(x), L_act=hi, x=x, act=hi - L_stand, chain=x - x0,
                    state='가열이나 메쉬 리미터 — 사슬이 장력을 정한다')
    elif g(lo) >= 0:
        L_act = lo
    else:
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            if g(mid) > 0:
                hi = mid
            else:
                lo = mid
        L_act = 0.5 * (lo + hi)
    x = max(0.0, x0 + dL - (L_act - L_stand))
    return dict(F=f_hot(L_act, F_hot_), L_act=L_act, x=x,
                act=L_act - L_stand, chain=x - x0, state='가열 평형')


# ── 3관찰 중 O1·O2 (기하·힘 평형만) ────────────────────────────────
DL_STOOP = 150.0        # mm — 사용자 줄자 실측 (직립 → 스툽)
O1_BAND = (10.0, 15.0)  # mm — 직립 60 ℃ 가열 시 허벅지 밴드 상승
O2_BAND_MAX = 20.0      # mm — 미가열 스툽에서 밴드 상승 해석 상한
O2_F_MAX = 100.0        # N — 미가열 스툽 장력 허용 상한 (굽히기 저항 체감)
O2_RATIO = 0.5          # 수동 / 능동 비율 상한


def test(prm):
    o1 = solve(0.0, prm, heated=True)
    d_band = prm['L_stand'] - o1['L_act']          # 직립에서 구동부가 수축한 양
    cold = solve(DL_STOOP, prm, heated=False)
    hot = solve(DL_STOOP, prm, heated=True)
    ratio = cold['F'] / hot['F'] if hot['F'] > 1e-9 else np.inf
    phi = (O2_BAND_MAX / cold['chain']) if cold['chain'] > 1e-9 else np.inf
    p1 = O1_BAND[0] <= d_band <= O1_BAND[1]
    p2a = cold['F'] <= O2_F_MAX
    p2b = ratio <= O2_RATIO
    return dict(d_band=d_band, o1=bool(p1),
                cold_F=cold['F'], cold_act=cold['act'], cold_chain=cold['chain'],
                hot_F=hot['F'], hot_act=hot['act'], hot_chain=hot['chain'],
                ratio=float(ratio), phi_req=float(min(phi, 1.0)),
                o2a=bool(p2a), o2b=bool(p2b), o2=bool(p2a and p2b),
                pass_=bool(p1 and p2a and p2b), state_cold=cold['state'])


GRID = dict(
    L_stand=[140.0, 160.0, 180.0],
    F_plat=[10.0, 20.0, 40.0],
    F_hot=[100.0, 150.0, 200.0, 250.0],
)
# 선형은 지시대로 k=1/2/5 에서 시작하되, 실패 원인을 보이기 위해 연질 쪽을 넓힌다
CHAINS = ([Chain('lin', k=k) for k in (0.2, 0.3, 0.5, 0.8, 1.0, 2.0, 5.0)] +
          [Chain('bi', k1=k1, xk=xk, k2=k2)
           for k1 in (0.2, 0.3, 0.5, 0.8, 1.0, 2.0)
           for xk in (20.0, 60.0, 100.0, 140.0, 180.0)
           for k2 in (5.0, 10.0, 20.0)])


def scan():
    rows = []
    for Ls, Fp, Fh, ch in itertools.product(GRID['L_stand'], GRID['F_plat'],
                                            GRID['F_hot'], CHAINS):
        prm = dict(L_stand=Ls, F_plat=Fp, F_hot=Fh, chain=ch)
        r = test(prm)
        r.update(L_stand=Ls, F_plat=Fp, F_hot=Fh, chain=ch.label(),
                 chain_kind=ch.kind, chain_p=ch.p)
        rows.append(r)
    return rows


def main():
    rows = scan()
    n = len(rows)
    p1 = [r for r in rows if r['o1']]
    p12 = [r for r in rows if r['pass_']]
    lin = [r for r in rows if r['chain_kind'] == 'lin']
    lin_pass = [r for r in lin if r['pass_']]
    print('=' * 104)
    print(f'[O1·O2] 조합 {n}개 스캔 — 선형 {len(lin)} · 이중선형 {n - len(lin)}')
    print('=' * 104)
    print(f'  O1 (직립 가열 밴드 상승 10~15 mm) 통과            {len(p1):4d}')
    print(f'  O1 + O2 (미가열 스툽 힘·비율) 통과                {len(p12):4d}')
    print(f'  ★ 선형 사슬만으로 통과                            {len(lin_pass):4d}'
          f'  → {"가능" if lin_pass else "불가능 — 이중선형 필요"}')

    if lin:
        print('\n  선형 사슬 대표 (왜 안 되는가)')
        print(f"    {'k':>4s} {'L_stand':>8s} {'F_hot':>6s} {'직립밴드':>9s} "
              f"{'미가열 스툽 F':>13s} {'사슬 몫':>9s} {'O1':>4s} {'O2':>4s}")
        for r in lin:
            if r['F_plat'] != 20.0 or r['F_hot'] != 150.0:
                continue
            print(f"    {r['chain_p']['k']:4g} {r['L_stand']:8.0f} {r['F_hot']:6.0f} "
                  f"{r['d_band']:9.1f} {r['cold_F']:13.1f} {r['cold_chain']:9.1f} "
                  f"{'✅' if r['o1'] else '❌':>4s} "
                  f"{'✅' if r['o2a'] else '❌'}/{'✅' if r['o2b'] else '❌'}"
                  f"  비율 {r['ratio']:.2f}")

    if p12:
        print('\n' + '=' * 104)
        print(f'[통과 조합] {len(p12)}개 — 상위 20')
        print('=' * 104)
        print(f"  {'L_stand':>7s} {'F_plat':>6s} {'F_hot':>6s} {'사슬':>26s} "
              f"{'직립밴드':>8s} {'미가열F':>8s} {'가열F':>7s} {'수동/능동':>9s} "
              f"{'사슬몫':>7s} {'밴드분담':>8s}")
        for r in sorted(p12, key=lambda r: (r['ratio'], -r['hot_F']))[:20]:
            print(f"  {r['L_stand']:7.0f} {r['F_plat']:6.0f} {r['F_hot']:6.0f} "
                  f"{r['chain']:>26s} {r['d_band']:8.1f} {r['cold_F']:8.1f} "
                  f"{r['hot_F']:7.1f} {r['ratio']:9.2f} {r['cold_chain']:7.1f} "
                  f"{r['phi_req']:8.2f}")
    else:
        print('\n⚠️ O1·O2 를 동시에 만족하는 조합이 없다 — 충돌 지점 분석')
        print(f"  O1 만 통과 {len(p1)} · O2 만 통과 "
              f"{len([r for r in rows if r['o2']])}")

    print('\n' + '=' * 104)
    print('[민감도] O1 해석 — 직립 사슬 변형 중 밴드 상승 비율 φ1 을 1 미만으로 두면')
    print('=' * 104)
    print(f"  {'φ1':>5s} {'허용 사슬 변형 (mm)':>20s} {'O1 통과':>8s} {'O1+O2 통과':>11s}")
    sens = []
    for phi in (1.0, 0.8, 0.6, 0.4):
        lo, hi = O1_BAND[0] / phi, O1_BAND[1] / phi
        n1 = [r for r in rows if lo <= r['d_band'] <= hi]
        n12 = [r for r in n1 if r['o2a'] and r['o2b']]
        sens.append(dict(phi=phi, lo=lo, hi=hi, n1=len(n1), n12=len(n12)))
        print(f'  {phi:5.1f} {lo:9.1f} ~ {hi:<8.1f} {len(n1):8d} {len(n12):11d}')
    json.dump(dict(sens=sens, rows=rows), open(f'{OUT}/force_sens.json', 'w'),
              ensure_ascii=False, indent=1, default=str)

    json.dump([{k: v for k, v in r.items() if k != 'chain_p'} | {'chain_p': r['chain_p']}
               for r in rows], open(f'{OUT}/force_scan.json', 'w'),
              ensure_ascii=False, indent=1)
    print(f'\nSAVED {OUT}/force_scan.json')
    return rows


if __name__ == '__main__':
    main()
