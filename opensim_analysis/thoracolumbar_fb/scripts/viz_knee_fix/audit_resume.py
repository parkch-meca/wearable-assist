"""[0] 재개 전 조건 감사 — 이번 작업이 쓰는 모델·setup 을 실제 파일에서 읽어 대조.

audit_conditions 의 추출 함수를 그대로 재사용한다 (추측 금지, 파일에서만 읽는다).

대조 기준
  5동작 기저 모델   sha1[:12] = e5bb8ab98934   좌표 169 · 근육 620 (ES 76)
  5동작 실행 모델   sha1[:12] = ca12f321326e   척추 reserve opt 5 N·m
  다관절 기저 모델  ..._rom_elbow.osim         근육 620 + 팔꿈치 14 = 634
"""
import os
import sys
import hashlib
import json
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audit_conditions as AC

M = '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x'
TARGETS = [
    ('5동작 기저 (허리 단독 논문)', f'{M}/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix_rom.osim'),
    ('다관절 기저 (팔꿈치근 추가)', f'{M}/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix_rom_elbow.osim'),
    ('5동작 실행 (스툽 OFF)', '/data/romfix_unified/stoop_off/model_res_tight.osim'),
    ('5동작 실행 (스툽 ON 24 N·m)', '/data/romfix_unified/stoop_on/model_res_tight.osim'),
    ('5동작 실행 (들기 OFF)', '/data/romfix_unified/box_off/model_res_tight.osim'),
    ('16.5 N·m 실행 (couple16)', '/data/suit_16Nm/couple16/model_res_tight.osim'),
    ('다관절 실행 (운반 5조건)', '/data/suit_carry/model_res_tight.osim'),
]
SETUPS = [
    ('스툽 OFF', '/data/romfix_unified/stoop_off/setup.xml'),
    ('스툽 ON 24', '/data/romfix_unified/stoop_on/setup.xml'),
    ('16.5 couple16', '/data/suit_16Nm/couple16/setup.xml'),
    ('들기 OFF (5동작)', '/data/romfix_unified/box_off/setup.xml'),
    ('운반 OFF (다관절)', '/data/suit_carry/off/setup.xml'),
]
PDF = '/data/wearable-assist/docs/refs/복합관절 근력보조 슈트 구성.pdf'
EXPECT = {'base5': 'e5bb8ab98934', 'run5': 'ca12f321326e'}


def sha12(p):
    return hashlib.sha1(open(p, errors='ignore').read().encode()).hexdigest()[:12]


def arm_opt(path):
    """팔 좌표 reserve + 팔 내장 액추에이터 optimal_force 실측."""
    s = open(path, errors='ignore').read()
    out = {}
    for nm, b in re.findall(r'<CoordinateActuator name="([^"]+)">(.*?)</CoordinateActuator>',
                            s, re.S):
        mm = re.search(r'<optimal_force>([^<]+)</optimal_force>', b)
        if not mm:
            continue
        v = float(mm.group(1))
        base = nm.replace('reserve_', '')
        if base.startswith(('shoulder_elv', 'shoulder_rot', 'elv_angle',
                            'elbow_flexion', 'pro_sup')) or 'actuator' in nm:
            key = 'arm_reserve' if nm.startswith('reserve_') else 'arm_actuator'
            out.setdefault(key, set()).add(v)
    return {k: sorted(v) for k, v in out.items()}


def main():
    print('=' * 100)
    print('[0] 모델 감사 — 실제 .osim 파일에서 추출')
    print('=' * 100)
    rows = {}
    for lab, p in TARGETS:
        if not os.path.exists(p):
            print(f'  ⛔ {lab:30s} 파일 없음: {p}')
            continue
        d = AC.audit_model(p)
        h = sha12(p)
        d['sha12'] = h
        d['arm'] = arm_opt(p)
        rows[lab] = d
        es = None
        s = open(p, errors='ignore').read()
        es = len(re.findall(r'<(?:Thelen2003Muscle|Millard2012EquilibriumMuscle) name="'
                            r'(?:IL_|LTpL|LTpT)[^"]*">', s))
        print(f'\n  {lab}')
        print(f'    파일     {d["file"]}')
        print(f'    sha1[:12] {h}')
        print(f'    좌표 {d["n_coord"]} · 근육 {d["n_muscle"]} (ES {es}) · reserve {d["n_reserve"]}')
        print(f'    reserve opt {d["opt"]}')
        if d['arm']:
            print(f'    팔 opt {d["arm"]}')
        print(f'    쿠플러 {len(d["couplers"])}개 · M1 견갑 {d["M1_scapula"]}')

    print('\n' + '=' * 100)
    print('[0] 기대값 대조')
    print('=' * 100)
    ok = True
    for lab, key in (('5동작 기저 (허리 단독 논문)', 'base5'),
                     ('5동작 실행 (스툽 OFF)', 'run5'),
                     ('5동작 실행 (스툽 ON 24 N·m)', 'run5'),
                     ('5동작 실행 (들기 OFF)', 'run5'),
                     ('16.5 N·m 실행 (couple16)', 'run5')):
        got = rows.get(lab, {}).get('sha12')
        good = got == EXPECT[key]
        ok &= good
        print(f'  {"✅" if good else "❌"} {lab:32s} {got}  (기대 {EXPECT[key]})')

    e = rows.get('다관절 기저 (팔꿈치근 추가)', {})
    b = rows.get('5동작 기저 (허리 단독 논문)', {})
    if e and b:
        d_m = e['n_muscle'] - b['n_muscle']
        d_c = e['n_coord'] - b['n_coord']
        print(f'  {"✅" if (d_m == 14 and d_c == 0) else "❌"} 다관절 기저 = 5동작 기저 + 팔꿈치근  '
              f'근육 {b["n_muscle"]} → {e["n_muscle"]} (Δ{d_m:+d}) · 좌표 Δ{d_c:+d}')

    c = rows.get('다관절 실행 (운반 5조건)', {})
    if c:
        arm = c['arm']
        good = arm.get('arm_reserve') == [5.0] and arm.get('arm_actuator') == [5.0]
        print(f'  {"✅" if good else "❌"} 다관절 실행 팔 자유도 전부 opt5  {arm}')
        good2 = c['opt'].get('spine') == [5.0]
        print(f'  {"✅" if good2 else "❌"} 다관절 실행 척추 reserve opt5  {c["opt"].get("spine")}')

    print('\n' + '=' * 100)
    print('[0] setup 감사 — 해석 조건')
    print('=' * 100)
    print(f'  {"조건":18s} {"t0":>5s} {"t1":>5s} {"lp":>5s} {"수렴":>8s} {"act_exp":>7s}  모션')
    for lab, p in SETUPS:
        if not os.path.exists(p):
            print(f'  ⛔ {lab:18s} setup 없음')
            continue
        s = AC.audit_setup(p)
        mot = os.path.basename(s['coords_file'] or '—')
        print(f'  {lab:18s} {s["t0"]:>5s} {s["t1"]:>5s} {s["lowpass"]:>5s} '
              f'{str(s["conv"]):>8s} {str(s["act_exp"]):>7s}  {mot}')

    print('\n' + '=' * 100)
    print('[0] STATUS §3-3 — 복합관절 사양 PDF')
    print('=' * 100)
    if os.path.exists(PDF):
        n = len([f for f in os.listdir('/data/wearable-assist/docs/refs/pdf_pages')]) \
            if os.path.isdir('/data/wearable-assist/docs/refs/pdf_pages') else 0
        print(f'  ✅ 존재 — {PDF}')
        print(f'     {os.path.getsize(PDF)/1e6:.2f} MB · 렌더 페이지 {n}개 '
              f'(docs/refs/pdf_pages/)')
        print('     → STATUS §3 항목 3 (재업로드 요청) 해제')
    else:
        print(f'  ❌ 없음 — {PDF}')
        ok = False

    print(f'\n판정: {"✅ 조건 정합 — 진행 가능" if ok else "❌ 불일치 — 중단 검토"}')
    json.dump({k: {kk: vv for kk, vv in v.items() if kk != 'control'}
               for k, v in rows.items()},
              open('/data/suit_dose/audit_resume.json', 'w'), ensure_ascii=False,
              indent=1, default=str)


if __name__ == '__main__':
    os.makedirs('/data/suit_dose', exist_ok=True)
    main()
