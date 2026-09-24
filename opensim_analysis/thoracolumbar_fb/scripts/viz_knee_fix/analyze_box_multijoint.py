"""[3] 들기 20 kg 다부위 기여 분해 — 운반과 **같은 분석 코드**로 5조건.

analyze_carry_multijoint 의 함수를 그대로 호출하고 디렉터리·라벨만 바꾼다.
지표 정의(창·3지표·주동근군·가산성 검정)를 복제하지 않아야 두 동작을 비교할 수 있다.

판정 대상 (운반에서 나온 결론이 들기에서도 재현되는가)
  (a) 가산성      전체 ON = 허리 단독 + 팔꿈치 단독 (운반 차이 0.16 %)
  (b) 스팬 불일치  팔꿈치 기본안에서 삼각근 증가(운반 +6.9 %), 연장안에서 해소(−1.8 %)
재현이든 불재현이든 그대로 보고한다.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze_carry_multijoint as AC

AC.D = '/data/suit_box'
AC.LAB = {'off': 'OFF', 'waist': '허리만 (T8→천골→허벅지)', 'elbow': '팔꿈치만 (기본안)',
          'elbow_ext': '팔꿈치만 (연장안)', 'all': '전체 ON (허리+팔꿈치 연장안)'}

if __name__ == '__main__':
    print('들기 20 kg 다부위 — /data/suit_box  (운반과 동일 분석 코드)')
    AC.main()
