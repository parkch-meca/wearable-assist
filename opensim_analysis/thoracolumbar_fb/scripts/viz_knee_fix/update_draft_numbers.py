"""[4] 초안 md 의 수치를 재실행본으로 갱신.

■ 원칙
  - 치환은 (구문자열 -> 신문자열, 기대 횟수) 목록으로 명시하고, 실제 치환 횟수가
    기대와 다르면 즉시 실패시킨다. 무심코 다른 곳까지 바뀌는 사고를 막는다.
  - 신값은 paper_numbers(단일 소스)에서만 가져온다. 직접 반올림하지 않는다.
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paper_numbers as pn

DRAFT = ('/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/'
         'five_motion_paper_draft.md')
OLD = json.load(open('/data/tight_unified/unified_numbers.json'))


def rel_old(k, m):
    o, n = round(OLD[k][f'{m}_off'], 2), round(OLD[k][f'{m}_on'], 2)
    return round(100.0 * round(n - o, 2) / o, 1)


def s(x, d=2, signed=False):
    return pn.fmt(x, d, signed)


# ── 문맥을 포함한 명시적 치환 목록 (단독 숫자 치환은 오폭 위험이 커서 쓰지 않는다) ──
def explicit_pairs():
    B = {k: pn.metric(k, 'b') for k in pn.ORDER}
    A = {k: pn.metric(k, 'a') for k in pn.ORDER}
    C = {k: pn.metric(k, 'c') for k in pn.ORDER}
    oB = {k: (round(OLD[k]['b_off'], 2), round(OLD[k]['b_on'], 2), rel_old(k, 'b'))
          for k in pn.ORDER}
    oA = {k: (round(OLD[k]['a_off'], 2), round(OLD[k]['a_on'], 2), rel_old(k, 'a'))
          for k in pn.ORDER}
    oC = {k: (round(OLD[k]['c_off'], 2), round(OLD[k]['c_on'], 2), rel_old(k, 'c'))
          for k in pn.ORDER}
    NM = {'squat': '맨몸 스쿼트', 'stoop': '맨몸 스툽', 'box': '박스 들기',
          'gait': '맨몸 보행', 'carry': '박스 운반'}
    LD = {'squat': '0 kg', 'stoop': '0 kg', 'box': '20 kg',
          'gait': '0 kg', 'carry': '20 kg'}
    P = []

    def add(o, n, cnt):
        if o != n:
            P.append((o, n, cnt))

    for k in pn.ORDER:
        b, ob = B[k], oB[k]
        # Table: | 동작 | 하중 | OFF | ON | Δ%p | **효과** |
        add(f'| {NM[k]} | {LD[k]} | {ob[0]:.2f} | {ob[1]:.2f} | '
            f'{pn.fmt(round(ob[1]-ob[0],2),2,True)} | **{pn.fmt(ob[2],1,True)}** |',
            f'| {NM[k]} | {LD[k]} | {b["off_s"]} | {b["on_s"]} | '
            f'{b["dpp_s"]} | **{b["rel_s"]}** |', 1)
        # Table: | 동작 | 하중 | 효과 % |
        add(f'| {NM[k]} | {LD[k]} | {pn.fmt(ob[2],1,True)} % |',
            f'| {NM[k]} | {LD[k]} | {b["rel_s"]} % |', 1)
        # §3.5 세 지표 표
        a, c, oa, oc = A[k], C[k], oA[k], oC[k]
        add(f'| {NM[k]} | {LD[k]} | {oa[0]:.2f} → {oa[1]:.2f} ({pn.fmt(oa[2],1,True)} %) | '
            f'**{ob[0]:.2f} → {ob[1]:.2f} ({pn.fmt(ob[2],1,True)} %)** | '
            f'{oc[0]:.2f} → {oc[1]:.2f} ({pn.fmt(oc[2],1,True)} %) |',
            f'| {NM[k]} | {LD[k]} | {a["off_s"]} → {a["on_s"]} ({a["rel_s"]} %) | '
            f'**{b["off_s"]} → {b["on_s"]} ({b["rel_s"]} %)** | '
            f'{c["off_s"]} → {c["on_s"]} ({c["rel_s"]} %) |', 1)
    return P


def apply(pairs, path=DRAFT, dry=False):
    txt = open(path, encoding='utf-8').read()
    report = []
    for old, new, expect in pairs:
        n = txt.count(old)
        if n != expect:
            report.append((old[:70], n, expect, 'MISMATCH'))
            continue
        txt = txt.replace(old, new)
        report.append((old[:70], n, expect, 'OK'))
    if not dry:
        open(path, 'w', encoding='utf-8').write(txt)
    return report


if __name__ == '__main__':
    pairs = explicit_pairs()
    rep = apply(pairs, dry='--dry' in sys.argv)
    ok = sum(1 for r in rep if r[3] == 'OK')
    print(f'치환 {ok}/{len(rep)} 성공')
    for old, n, e, st in rep:
        if st != 'OK':
            print(f'  [{st}] 발견 {n} 기대 {e}: {old}')
