"""tight reserve 통일 후 5동작 재평가 + 이전(혼재) 값과의 대조.

새 해석 실행 없음 — /data/tight_rerun/ (신규) 과 기존 결과 .sto 를 읽어 서술만 한다.
"""
import numpy as np, opensim as osim, os, json

SPINE_KEYS = ('_FE', '_LB', '_AR', 'Abs_')


def load(p):
    t = osim.TimeSeriesTable(p)
    T = np.array(list(t.getIndependentColumn())); labs = list(t.getColumnLabels())
    D = {c: np.array([float(t.getDependentColumn(c)[i]) for i in range(t.getNumRows())])
         for c in labs}
    return T, D, labs


def es(D, labs):
    E = [l for l in labs if l.startswith(('IL_', 'LTpL', 'LTpT'))]
    S = np.vstack([D[e] for e in E])
    return S.max(axis=0) * 100, S.mean(axis=0) * 100, len(E)


def spine_res(p):
    if not os.path.exists(p):
        return None, None
    _, F, fl = load(p)
    r = [l for l in fl if l.startswith('reserve_') and any(k in l for k in SPINE_KEYS)]
    if not r:
        return None, None
    v, nm = max((float(np.abs(F[x]).max()), x) for x in r)
    return v, nm.replace('reserve_', '')


# 신규(tight 통일) / 기존(혼재) 결과 경로
NEW = {k: (f'/data/tight_rerun/{k}_off/so_StaticOptimization_%s.sto',
           f'/data/tight_rerun/{k}_on/so_StaticOptimization_%s.sto')
       for k in ('squat', 'stoop', 'box')}
NEW['gait'] = ('/data/gait_results/gait_off_tight/so_StaticOptimization_%s.sto',
               '/data/gait_results/gait_on_tight/so_StaticOptimization_%s.sto')
NEW['carry'] = ('/data/carry_results/carry_off/so_StaticOptimization_%s.sto',
                '/data/carry_results/carry_on/so_StaticOptimization_%s.sto')

OLD = {
 'squat': ('/data/squat_results/suit_sweep/F0/squat_F0_StaticOptimization_%s.sto',
           '/data/squat_results/suit_sweep/F200/squat_F200_StaticOptimization_%s.sto'),
 'stoop': ('/data/stoop_results/stoop_v5/so_v5_StaticOptimization_%s.sto',
           '/data/stoop_results/suit_sweep_v5/F200/suit_v5_F200_StaticOptimization_%s.sto'),
 'box':   ('/data/stoop_results/box_stoop_so/B_off/so_B_off_StaticOptimization_%s.sto',
           '/data/stoop_results/box_stoop_so/B_on/so_B_on_StaticOptimization_%s.sto'),
 'gait':  NEW['gait'], 'carry': NEW['carry'],
}

# 대표 시점 정의 (기존 논문/발표와 동일)
WIN = {
 'squat': [('최대 하강 시점', 'inst'), ('전주기 정점', 'peak')],
 'stoop': [('최대 굴곡 시점', 'inst'), ('전주기 정점', 'peak')],
 'box':   [('최대 하중 시점', ('lpeak', 1.9, 5.9)), ('하중 구간 평균', ('wmean', 1.9, 5.9))],
 'gait':  [('heel strike', ('wpeak', 0.62, 0.74)), ('mid-stance', ('wpeak', 0.94, 1.06)),
           ('toe-off', ('wpeak', 1.30, 1.42)), ('전주기', ('wpeak', 0.40, 1.60))],
 'carry': [('heel strike', ('wpeak', 0.62, 0.74)), ('mid-stance', ('wpeak', 0.94, 1.06)),
           ('toe-off', ('wpeak', 1.30, 1.42)), ('전주기', ('wpeak', 0.40, 1.60))],
}
NAME = {'squat': '맨몸 스쿼트', 'stoop': '맨몸 스툽', 'box': '박스 들기',
        'gait': '맨몸 보행', 'carry': '박스 운반'}


def measure(pa, pb, specs):
    Ta, Da, La = load(pa % 'activation'); Tb, Db, Lb = load(pb % 'activation')
    pk_a, mn_a, n = es(Da, La); pk_b, mn_b, _ = es(Db, Lb)
    rows = []
    for nm, spec in specs:
        if spec == 'inst':
            rel = 100 * (pk_b - pk_a) / np.maximum(pk_a, 1e-9)
            i = int(np.argmin(rel)); o, v, at = pk_a[i], pk_b[i], f't={Ta[i]:.2f}s'
        elif spec == 'peak':
            o, v, at = pk_a.max(), pk_b.max(), '전주기 max'
        else:
            mode, lo, hi = spec
            ma = (Ta >= lo) & (Ta <= hi); mb = (Tb >= lo) & (Tb <= hi)
            if mode == 'lpeak':
                i = int(np.argmax(np.where(ma, pk_a, -1)))
                o, v, at = pk_a[i], pk_b[i], f't={Ta[i]:.2f}s'
            elif mode == 'wmean':
                o, v, at = pk_a[ma].mean(), pk_b[mb].mean(), f'{lo}-{hi}s 평균'
            else:
                o, v, at = pk_a[ma].max(), pk_b[mb].max(), f'{lo}-{hi}s max'
        dp = v - o
        rows.append(dict(name=nm, at=at, off=float(o), on=float(v), dpp=float(dp),
                         drel=float(100 * dp / o) if o > 1e-9 else float('nan')))
    return rows, float(mn_a.max()), float(mn_b.max()), n


res = {}
print('=' * 100)
print('[1] tight reserve 통일 결과 (5동작)')
print('=' * 100)
for k in ('squat', 'stoop', 'box', 'gait', 'carry'):
    pa, pb = NEW[k]
    if not os.path.exists(pa % 'activation'):
        print(f'{NAME[k]}: 결과 없음 ({pa})'); continue
    rows, mo, mn, n = measure(pa, pb, WIN[k])
    sr_o, nm_o = spine_res(pa % 'force'); sr_n, _ = spine_res(pb % 'force')
    print(f'\n### {NAME[k]} (nES={n})   spine reserve OFF {sr_o:.2f} / ON {sr_n:.2f} N·m  [{nm_o}]')
    for r in rows:
        print(f"   {r['name']:16s} [{r['at']:14s}] OFF {r['off']:7.2f}  ON {r['on']:7.2f}"
              f"  Δ {r['dpp']:+7.2f} %p  ({r['drel']:+6.1f} %)")
    print(f"   ES_mean 전주기 max        OFF {mo:7.2f}  ON {mn:7.2f}"
          f"  ({100*(mn-mo)/mo:+6.1f} %)")
    res[k] = dict(rows=rows, es_mean_off=mo, es_mean_on=mn,
                  es_mean_rel=100 * (mn - mo) / mo,
                  spine_res_off=sr_o, spine_res_on=sr_n, n_es=n)

print('\n' + '=' * 100)
print('[2] 이전(reserve 혼재) vs 신규(tight 통일) 대조 — 대표 지표')
print('=' * 100)
HEAD = f"{'동작':12s} {'대표 시점':16s} {'이전 OFF':>9s} {'이전 ON':>8s} {'이전 Δ%':>8s} " \
       f"{'신규 OFF':>9s} {'신규 ON':>8s} {'신규 Δ%':>8s} {'Δ%의 변화':>10s}"
print(HEAD); print('-' * len(HEAD))
cmp = {}
for k in ('squat', 'stoop', 'box', 'gait', 'carry'):
    if k not in res: continue
    oa, ob = OLD[k]
    if not os.path.exists(oa % 'activation'): continue
    orows, _, _, _ = measure(oa, ob, WIN[k])
    sr_old, _ = spine_res(oa % 'force')
    cmp[k] = dict(old=orows, new=res[k]['rows'], spine_old=sr_old,
                  spine_new=res[k]['spine_res_off'])
    for o, nn in zip(orows, res[k]['rows']):
        print(f"{NAME[k]:12s} {o['name']:16s} {o['off']:9.2f} {o['on']:8.2f} {o['drel']:+8.1f} "
              f"{nn['off']:9.2f} {nn['on']:8.2f} {nn['drel']:+8.1f} {nn['drel']-o['drel']:+10.1f}")
    print(f"{'':12s} {'spine reserve':16s} {sr_old:9.2f} {'':8s} {'':8s} "
          f"{res[k]['spine_res_off']:9.2f}")

print('\n' + '=' * 100)
print('[3] 부하–효과 단조성 판정 (tight 통일, 대표값)')
print('=' * 100)
REP = {'squat': 0, 'stoop': 0, 'box': 0, 'carry': 1, 'gait': 3}   # 대표 행 index
order = []
for k in ('squat', 'stoop', 'carry', 'box', 'gait'):
    if k not in res: continue
    r = res[k]['rows'][REP[k]]
    order.append((NAME[k], r['name'], r['drel'], r['dpp']))
order_sorted = sorted(order, key=lambda x: -x[2])
print(f"{'동작':12s} {'대표 시점':16s} {'Δ% (감소율)':>12s} {'Δ%p (절대)':>12s}")
for nm, at, dr, dp in order_sorted:
    print(f"{nm:12s} {at:16s} {dr:12.1f} {dp:12.2f}")
LOADED = ['맨몸 스쿼트', '맨몸 스툽', '박스 운반', '박스 들기']
vals = [(nm, dr) for nm, at, dr, dp in order_sorted if nm in LOADED]
mono = all(vals[i][1] <= vals[i + 1][1] + 1e-9 for i in range(len(vals) - 1))
print(f"\n부하 있는 4동작 감소율 순서: {' > '.join(f'{n}({abs(v):.1f}%)' for n, v in vals)}")
print(f"부하 증가에 따른 단조 감소 성립: {'YES' if mono else 'NO'}")
absv = [dp for nm, at, dr, dp in order_sorted if nm in LOADED]
print(f"절대 감소량 범위: {min(absv):.2f} ~ {max(absv):.2f} %p (폭 {max(absv)-min(absv):.2f})")

P = '/data/tight_rerun/tight_unified_numbers.json'
json.dump(dict(new=res, cmp=cmp), open(P, 'w'), ensure_ascii=False, indent=1, default=float)
print('\nSAVED', P)
