"""논문·발표자료 공통 수치 모듈 — 표기 규칙을 한 곳에서 강제한다.

■ 문제
  파생값(Δ, 상대 %)을 미반올림 원값으로 계산하고 baseline은 반올림해 인쇄하면,
  독자가 인쇄된 값으로 재계산했을 때 결과가 어긋난다(실제 7곳 발생).

■ 표기 규칙 (전 문서 공통)
  1. 활성도(OFF/ON, %)          : 소수 2자리
  2. 절대차 Δ (%p)              : **인쇄된 2자리 값의 차**, 소수 2자리
  3. 상대 변화율 (%)            : **인쇄된 2자리 값에서 계산**, 소수 1자리
  4. reserve (N·m)              : 소수 2자리
  5. 근육군 합계 (%)            : 소수 2자리, 변화율은 규칙 3과 동일
  → 인쇄된 숫자만으로 모든 파생값을 재현할 수 있다.

이 모듈이 반환하는 값만 사용할 것. 직접 반올림하지 말 것.
"""
import json
import os as _os

# ── 결과 루트 (단일 소스) ────────────────────────────────────────
# 2026-08-03: ROM 부호 수정 + 좌팔 운동학 수정 재실행본으로 교체.
#   이전: /data/tight_unified (좌팔 미러 오류가 스툽·박스 들기·박스 운반에 남아 있던 상태)
#   스쿼트·보행은 운동학이 바뀌지 않았고 재실행 결과가 이전과 일치함(회귀 검증).
RESULTS = '/data/romfix_unified'

# .sto 경로 — figure 생성 스크립트도 이 표를 쓴다 (경로가 갈라지지 않게)
STO = {k: (f'{RESULTS}/{k}_off/so_StaticOptimization_activation.sto',
           f'{RESULTS}/{k}_on/so_StaticOptimization_activation.sto')
       for k in ('squat', 'stoop', 'box', 'gait', 'carry')}

U = json.load(open(f'{RESULTS}/unified_numbers.json'))
G = json.load(open(f'{RESULTS}/gait_redistribution.json'))

NAME = {'squat': '맨몸 스쿼트', 'stoop': '맨몸 스툽', 'box': '박스 들기',
        'gait': '맨몸 보행', 'carry': '박스 운반'}
LOAD = {'squat': '0 kg', 'stoop': '0 kg', 'box': '20 kg',
        'gait': '0 kg', 'carry': '20 kg'}
ORDER = ['squat', 'stoop', 'box', 'gait', 'carry']      # 전 표·그림 공통 순서
MINUS = '−'                                        # 음수 기호 통일


def _r2(x):
    return round(float(x), 2)


def fmt(x, d=2, signed=False):
    """음수 기호를 U+2212로 통일한 문자열."""
    s = f'{x:+.{d}f}' if signed else f'{x:.{d}f}'
    return s.replace('-', MINUS)


def metric(key, m):
    """동작 key, 지표 m ∈ {a,b,c} → 규칙에 맞춘 값 묶음.
    off/on은 2자리로 반올림한 뒤, dpp와 rel을 그 값에서 계산한다."""
    off = _r2(U[key][f'{m}_off'])
    on = _r2(U[key][f'{m}_on'])
    dpp = _r2(on - off)
    rel = round(100.0 * dpp / off, 1)
    return dict(off=off, on=on, dpp=dpp, rel=rel,
                off_s=fmt(off), on_s=fmt(on),
                dpp_s=fmt(dpp, 2, signed=True), rel_s=fmt(rel, 1, signed=True))


def reserve(key):
    return _r2(U[key]['res'])


def gait_group(name):
    """보행 근육군: (OFF, ON, Δ%p, Δ%) — 규칙 적용."""
    off, on, n = G['groups'][name]
    off, on = _r2(off), _r2(on)
    dpp = _r2(on - off)
    return dict(off=off, on=on, n=n, dpp=dpp,
                rel=round(100.0 * dpp / off, 1),
                off_s=fmt(off), on_s=fmt(on),
                rel_s=fmt(round(100.0 * dpp / off, 1), 1, signed=True))


def gait_phase(idx):
    """보행 구간별 — peak/mean/집중도. 집중도도 인쇄된 2자리 값에서 계산."""
    r = G['phases'][idx]
    po, pn = _r2(r['peak_off']), _r2(r['peak_on'])
    mo, mn = _r2(r['mean_off']), _r2(r['mean_on'])
    return dict(phase=r['phase'],
                peak_off=po, peak_on=pn,
                peak_rel=round(100.0 * _r2(pn - po) / po, 1),
                mean_off=mo, mean_on=mn,
                mean_rel=round(100.0 * _r2(mn - mo) / mo, 1),
                conc_off=round(po / mo, 2), conc_on=round(pn / mn, 2))


# 보행 재분배 총계 — 근육군 합에서 직접 유도 (문서 간 불일치 방지)
_g = {k: gait_group(k) for k in G['groups']}
GAIT_TOTAL_OFF = _r2(sum(v['off'] for v in _g.values()))
GAIT_TOTAL_ON = _r2(sum(v['on'] for v in _g.values()))
GAIT_TOTAL_DPP = _r2(GAIT_TOTAL_ON - GAIT_TOTAL_OFF)

# reserve 민감도 (보행) — 고정 관측값
RES_SENS = {
    'std': dict(reserve=16.78, off=11.13, on=5.54),
    'tight': dict(reserve=1.01, off=35.08, on=34.11),
}
for v in RES_SENS.values():
    v['dpp'] = _r2(v['on'] - v['off'])
    v['dpp_s'] = fmt(v['dpp'], 2, signed=True)
RES_RATIO = round(RES_SENS['tight']['off'] / RES_SENS['std']['off'], 1)   # 3.2


# ══════════════════════════════════════════════════════════════════
# 복합관절 연구 — 슈트 기하 재산출 (L-01 (C) 병기 확정, 2026-08-16)
#
# 5동작 논문의 24 N·m 는 "설계 목표 조건"이고, 아래는 "현 하드웨어 조건"이다.
# 두 조건은 토크를 독립변수로 둔 용량–반응 곡선 위의 두 지점이며,
# 어느 한쪽이 다른 쪽을 무효화하지 않는다. 자세한 근거는
# docs/KNOWN_LIMITATIONS.md L-01 참조.
# ══════════════════════════════════════════════════════════════════
SUIT_DESIGN_TORQUE = 24.0            # N·m — 설계 목표 조건 (200 N × 0.12 m 가정)
SUIT_DESIGN_MA = 120.0               # mm  — 그 가정이 요구하는 모멘트 암
SUIT_HW_MA = (79.0, 89.0)            # mm  — 재산출 모멘트 암 (요추 5레벨)
SUIT_HW_TORQUE = (15.7, 17.8)        # N·m — 현 하드웨어 조건 (양측 합)
SUIT_HW_TORQUE_MID = 16.5            # N·m — 중앙값
ES_MAX_MA = 77.0                     # mm  — 같은 모델 ES 근속 최대 모멘트 암

_S16 = '/data/suit_16Nm/results.json'
SUIT16 = json.load(open(_S16)) if _os.path.exists(_S16) else None


def suit_condition(which):
    """'design' | 'hw' → (토크 N·m, 모멘트암 mm, 설명)."""
    if which == 'design':
        return SUIT_DESIGN_TORQUE, SUIT_DESIGN_MA, '설계 목표 조건'
    return SUIT_HW_TORQUE_MID, sum(SUIT_HW_MA) / 2, '현 하드웨어 조건'


def suit16(key):
    """16 N·m 실검증·설계 레버 결과. key ∈ {ref24, path16, couple16, leverA/B/C}."""
    if SUIT16 is None:
        raise RuntimeError('16 N·m 실검증 결과가 아직 없다 — run_suit16.py 실행 필요')
    d = SUIT16[key]
    if key == 'ref24':
        return dict(off=_r2(d['off']), on=_r2(d['on']), eff=d['eff'],
                    torque=d['torque'], label='설계 목표 조건 24 N·m')
    return dict(off=_r2(d['off']), on=_r2(d['on']), eff=d['eff'],
                torque=d['torque'], label=d['label'])


if __name__ == '__main__':
    print('규칙 적용 후 — 인쇄값으로 재계산 시 일치 여부 점검')
    bad = 0
    for k in ORDER:
        for m in ('a', 'b', 'c'):
            d = metric(k, m)
            chk = round(100.0 * round(d['on'] - d['off'], 2) / d['off'], 1)
            ok = abs(chk - d['rel']) < 1e-9
            bad += (not ok)
            print(f"  {NAME[k]:8s}({m}) {d['off_s']:>7s} → {d['on_s']:>7s}  "
                  f"Δ {d['dpp_s']:>8s} %p  {d['rel_s']:>7s} %   {'OK' if ok else '불일치'}")
    for i in range(len(G['phases'])):
        p = gait_phase(i)
        chk = round(100.0 * round(p['mean_on'] - p['mean_off'], 2) / p['mean_off'], 1)
        ok = abs(chk - p['mean_rel']) < 1e-9
        bad += (not ok)
    print(f"\n보행 총계: {GAIT_TOTAL_OFF} → {GAIT_TOTAL_ON} = {fmt(GAIT_TOTAL_DPP,2,True)} %p")
    print(f"reserve 민감도: 표준 {RES_SENS['std']['dpp_s']} %p / "
          f"tight {RES_SENS['tight']['dpp_s']} %p, 과소평가 배수 {RES_RATIO}")
    print(f"\n불일치 {bad}건")
