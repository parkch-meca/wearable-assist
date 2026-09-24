"""[3] 들기 20 kg 다부위 조건 생성 — 운반과 완전히 같은 코드 경로로 5조건.

■ 운반과 무엇이 같고 무엇이 다른가
  같다 : 허리 = 조건 B(T8 → 천골 경유 → 허벅지) · 팔꿈치 기본안/연장안 · 어깨 제외
         직렬 탄성 k = 5 N/mm · 경로점 산출 함수 · 외력 작성 방식 (suit_multijoint_conditions
         의 함수를 그대로 호출한다 — 복제하지 않는다)
  다르다: 동작(box_stoop_lift_m1_armfix) · 시간범위(0~7.5 s) · 기존 외력(박스 손 하중, GRF 없음)
         **팔꿈치 기준장 피팅 자세**

■ ⭐ 피팅 자세 — 들기는 중립 기립 피팅으로 충분하다 (운반과 다른 점)
  사전검증(precheck_box_multijoint) 실측:
    창 2.333~5.433 s · 창내 팔꿈치 32.0° (20~62°) · 어깨 elv_angle 26.6°
  이완각(팔꿈치 70° · 어깨 80°) **이내**다. 즉 해부학적 중립(0°)에서 조여 입어도
  작업 구간에서 장력이 살아 있다 → 허리와 같은 'neutral' 피팅을 쓴다.
  ※ 운반은 창내 팔꿈치가 97.9° 로 이완각을 넘어 작업 자세 피팅이 불가피했다 (L-11).
    들기 프레임 0 의 팔꿈치 경로장(378.0 mm)이 중립 기립 기준장과 소수점까지 일치함을
    확인했으므로, 두 규칙이 들기에서 같은 값을 준다.

■ 조건
  off        외력 = 박스 손 하중만 (기존 5동작 들기 OFF 와 동일)
  waist      + 허리 T8 → 천골 경유 → 허벅지
  elbow      + 팔꿈치 상완→전완 (기본안)
  elbow_ext  + 팔꿈치 견갑→상완→전완 (스팬 정합 연장안)
  all        허리 + 팔꿈치 연장안
"""
import os
import re
import sys
import json
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suit_multijoint_conditions as MC
import suit_span_conditions as SC

OUT = '/data/suit_box'
MOT = '/data/stoop_motion/box_stoop_lift_m1_armfix.mot'
EXT_SRC = '/data/romfix_unified/box_off/ext_B_off.xml'
EXT_DATA = '/data/romfix_unified/box_off/ext_B_off.mot'
T0, T1 = 0.0, 7.5


def box_force_objects():
    """기존 들기 외력(박스 손 하중 좌우) 블록 — data_source_name 은 떼고 datafile 로 통일."""
    txt = open(EXT_SRC).read()
    objs = re.findall(r'<ExternalForce name="[^"]*">.*?</ExternalForce>', txt, re.S)
    objs = [re.sub(r'<data_source_name>[^<]*</data_source_name>', '', o) for o in objs]
    return objs, EXT_DATA


def patch():
    """운반 모듈의 상수만 들기용으로 바꾼다 — 계산 함수는 건드리지 않는다."""
    MC.OUT = OUT
    MC.MOT = MOT
    MC.EXT_SRC = EXT_SRC
    MC.T0, MC.T1 = T0, T1
    MC.carry_force_objects = box_force_objects
    # 팔꿈치도 중립 기립 피팅 — 위 §피팅 자세 참조
    _orig = MC.path_series

    def neutral_fit(m, cs, bs, K, T, P, k_ser, fit='neutral'):
        return _orig(m, cs, bs, K, T, P, k_ser, 'neutral')
    MC.path_series = neutral_fit
    os.makedirs(OUT, exist_ok=True)


if __name__ == '__main__':
    patch()
    only = [a for a in sys.argv[1:] if not a.startswith('--')]
    summary = {}
    for tag, parts in MC.CONDS.items():
        if only and tag not in only:
            continue
        info = MC.build(tag, parts)
        summary[tag] = info
        desc = ' + '.join(parts) if parts else '외력 없음(기존 들기 OFF 와 동일)'
        print(f'[{tag}] {desc}', flush=True)
        for k, v in info.items():
            print(f"    {k}: 경로점 {v['n_pts']}개  L {v['L_min']:.1f}~{v['L_max']:.1f} mm "
                  f"(기준 {v['L0']:.1f})  장력 {v['tens_min']:.1f}~{v['tens_max']:.1f} N  "
                  f"평균 {v['tens_mean']:.1f} N", flush=True)
    p = f'{OUT}/build_info.json'
    if os.path.exists(p) and only:
        old = json.load(open(p))
        old.update(summary)
        summary = old
    json.dump(summary, open(p, 'w'), ensure_ascii=False, indent=1)
    print(f'\nSAVED {OUT}/ext_*.{{mot,xml}}  +  build_info.json')
