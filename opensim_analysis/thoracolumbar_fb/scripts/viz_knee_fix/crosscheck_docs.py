"""[4] 문서 간 수치 일관성 자동 대조.

논문 초안(md) · 논문 docx · 논문 pdf · 발표자료 pptx · 완결기록(md) 에서 텍스트를 추출해,
paper_numbers(단일 소스)가 규정한 값이 그대로 들어 있는지, 그리고 폐기된 구값이
남아 있지 않은지 검사한다.
"""
import os
import re
import sys
import json
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paper_numbers as pn

ROOT = '/data/wearable-assist/opensim_analysis/thoracolumbar_fb'
DOCS = {
    '논문 초안(md)': f'{ROOT}/docs/five_motion_paper_draft.md',
    '완결기록(md)': f'{ROOT}/docs/five_motion_completion_record.md',
    '인계문서(md)': f'{ROOT}/docs/HANDOVER_multijoint.md',
    '논문 docx': f'{ROOT}/docs/five_motion_paper.docx',
    '논문 pdf': f'{ROOT}/docs/five_motion_paper.pdf',
    '발표자료 pptx': '/data/opensim_results/SMA_suit_5motion_presentation.pptx',
}
OLD = json.load(open('/data/tight_unified/unified_numbers.json'))


def text_of(path):
    if path.endswith('.md'):
        return open(path, encoding='utf-8').read()
    if path.endswith(('.docx', '.pptx')):
        out = []
        with zipfile.ZipFile(path) as z:
            for n in z.namelist():
                if re.match(r'(word/document|ppt/slides/slide\d+|ppt/charts/chart\d+)'
                            r'.*\.xml$', n):
                    out.append(re.sub(r'<[^>]+>', '', z.read(n).decode('utf-8', 'ignore')))
        return '\n'.join(out)
    if path.endswith('.pdf'):
        import subprocess
        r = subprocess.run(['pdftotext', path, '-'], capture_output=True)
        return r.stdout.decode('utf-8', 'ignore')
    return ''


def rel_old(k, m):
    o, n = round(OLD[k][f'{m}_off'], 2), round(OLD[k][f'{m}_on'], 2)
    return round(100.0 * round(n - o, 2) / o, 1)


def main():
    # 현재 유효한 값의 문자열 집합 — 구값이 여기에 겹치면 오탐이므로 제외한다
    # (예: 운반 (c) ON 구값 10.30 은 스툽 (c) ON 신값 10.30 과 같은 문자열이다)
    live = set()
    for k in pn.ORDER:
        for m in 'abc':
            d = pn.metric(k, m)
            live.update({d['off_s'], d['on_s'], d['rel_s'] + ' %', d['dpp_s']})
            # 초록 등은 1자리로 줄여 쓰므로 그 표기도 유효값으로 등록
            live.update({pn.fmt(round(d['off'], 1), 1), pn.fmt(round(d['on'], 1), 1)})

    # 폐기된 구값 — 값이 실제로 바뀐 것만 검사 대상에 넣는다
    stale = []
    for k in pn.ORDER:
        for m in 'abc':
            new = pn.metric(k, m)
            o_off, o_on = round(OLD[k][f'{m}_off'], 2), round(OLD[k][f'{m}_on'], 2)
            o_rel = rel_old(k, m)
            if abs(o_rel - new['rel']) > 0.049:
                ov = pn.fmt(o_rel, 1, True) + ' %'
                if ov not in live:
                    stale.append((f'{pn.NAME[k]} ({m}) 효과', ov, new['rel_s'] + ' %', False))
            for label, ovn, nvn in (('OFF', o_off, new['off']), ('ON', o_on, new['on'])):
                if abs(ovn - nvn) > 0.005:
                    for dec in (2, 1):          # 2자리 표기와 1자리(초록) 표기를 모두 검사
                        ov = pn.fmt(round(ovn, dec), dec)
                        nv = pn.fmt(round(nvn, dec), dec)
                        if ov == nv or ov in live:
                            continue
                        # 1자리는 짧아서 다른 수의 일부와 겹치기 쉽다 -> 앞뒤 경계를 요구
                        strict = dec == 1
                        stale.append((f'{pn.NAME[k]} ({m}) {label}', ov, nv, strict))

    print('=' * 96)
    print('[1] 폐기된 구값이 문서에 남아 있는가  (남아 있으면 실패)')
    print('=' * 96)
    print(f'  검사 대상 구값 {len(stale)}개')
    bad = 0
    for name, path in DOCS.items():
        if not os.path.exists(path):
            print(f'  {name:14s} 파일 없음')
            continue
        t = text_of(path)
        hits = []
        for label, ov, nv, strict in stale:
            # 구값 문자열이 신값과 다르고, 문서에 그대로 있으면 잔존
            pat = (r'(?<![0-9.\-\u2212])' + re.escape(ov) + r'(?=\s?%)') if strict \
                  else re.escape(ov)
            if ov != nv and re.search(pat, t):
                # '이전 판' 서술에서 의도적으로 인용한 경우는 제외
                ctxs = [m.start() for m in re.finditer(pat, t)]
                real = [c for c in ctxs
                        if not re.search(r'이전 판|정정 전|폐기|구값|v2\(|시점 값 기준|'
                                         r'인공물|산물이었다', t[max(0, c - 200):c])]
                if real:
                    hits.append(f'{label}={ov}')
        if hits:
            bad += 1
            print(f'  {name:14s} ❌ 잔존 {len(hits)}건: {", ".join(sorted(set(hits))[:6])}')
        else:
            print(f'  {name:14s} ✅ 잔존 없음')

    print('\n' + '=' * 96)
    print('[2] 확정 신값이 문서에 들어 있는가  (주 지표 효과 %)')
    print('=' * 96)
    print(f"  {'문서':14s} " + ' '.join(f'{pn.NAME[k]:>10s}' for k in pn.ORDER))
    for name, path in DOCS.items():
        if not os.path.exists(path):
            continue
        t = text_of(path)
        row = f'  {name:14s} '
        for k in pn.ORDER:
            v = pn.metric(k, 'b')['rel_s']
            # 발표자료는 '감소' 문맥이라 부호 없이 25.7 로 적는다 — 둘 다 인정
            found = (v in t) or (v.lstrip(pn.MINUS + '+') in t)
            row += f'{("있음 " + v) if found else ("없음 " + v):>12s}'
        print(row)

    print('\n' + '=' * 96)
    print(f'결과: {"모든 문서 일관 ✅" if bad == 0 else f"{bad}개 문서에 구값 잔존 ❌"}')
    return 0 if bad == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
