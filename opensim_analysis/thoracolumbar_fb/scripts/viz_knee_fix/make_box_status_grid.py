# ⛔ 정정 (2026-07-30): 이 스크립트가 그림에 새기는 "문헌 10–17 %(P3)" 대조는 오독이다.
#    Hasenmaier 2026의 10–27 %는 %MVC 절대 포인트이지 상대 감소율이 아니며,
#    stoop 상대 감소율은 −39.3 %, squat은 유의차 미보고로 대조 불가.
#    이 스크립트로 생성된 그림은 논문·발표에 사용 금지. 상세: docs/five_motion_paper_draft.md §4
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import matplotlib.image as mpimg
import numpy as np
kf="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
fm.fontManager.addfont(kf); plt.rcParams['font.family']=fm.FontProperties(fname=kf).get_name(); plt.rcParams['axes.unicode_minus']=False
def crop(p,pad=10):
    im=mpimg.imread(p); a=(im[:,:,:3]*255).astype(int); bg=a[2,2]
    m=np.abs(a-bg).sum(2)>26; ys,xs=np.where(m)
    return im[max(0,ys.min()-pad):ys.max()+pad, max(0,xs.min()-pad):xs.max()+pad]

fig=plt.figure(figsize=(16,10)); gs=fig.add_gridspec(2,2,height_ratios=[1.15,1.0],hspace=0.16,wspace=0.12)
fig.suptitle("박스 들기 모션 현황 — 사실 확인 (진행 방향 결정용)",fontsize=20,fontweight='bold',y=0.98)

axt=fig.add_subplot(gs[0,:]); axt.axis('off')
rows=[["모션","발 접지","손-박스 파지","OFF/ON SO","박스하중","시각","핵심 한계"],
 ["box_v2 (=stoop_box20kg_v2)","❌ 23cm 지하","❌ 손이 위","✅ box_lift_v2","✅","❌","발 매몰 + 박스 못 잡음"],
 ["box_v1 (box_motion)","❌ 9cm 지하","❌ 25cm 위","✅ box_lift","✅","❌","더 얕게 굽힘"],
 ["box_v11b","✅ 접지(-0.905)","얕은 굽힘","❌ 없음","(SO X)","✅ 8/8","SO 없음·ES 비교불가·동역학 3570N"],
 ["box_v6~v11","미검","미검","❌ 없음","-","부분","SO 없음"]]
tb=axt.table(cellText=rows,bbox=[0.02,0.30,0.96,0.62]); tb.auto_set_font_size(False); tb.set_fontsize(11.5)
for (r,c),cell in tb.get_celld().items():
    if r==0: cell.set_facecolor('#e8e8e8'); cell.set_text_props(fontweight='bold')
    if r==3: cell.set_facecolor('#e3f0e3')
    if r in (1,2): cell.set_facecolor('#fbe9e7')
    cell.set_edgecolor('#aaa')
axt.text(0.02,0.21,"핵심 딜레마: 'SO(ES색) 있는 모션(v2/v1)'은 발 매몰+박스 미파지 / '시각 좋은 v11b'는 SO 없음(closure: ES future work, 새 모션 시도 금지).",
         fontsize=13,color='#7a0000',fontweight='bold')
axt.text(0.02,0.11,"한 모션이 '발 접지'와 '손이 박스 닿기'를 동시에 만족 못 함 — 약 15cm 부족(충분히 깊이 못 굽힘). 진단 문서 box_motion_v2_diagnostic.md 일치.",
         fontsize=12,color='#333')
axt.text(0.02,0.02,"슈트 효과(참고): box_v2(고부하) ES peak 0.80, 감소 11% — 문헌 10–17%(P3) 일치. 단 위 시각 한계로 '일반인 영상'엔 부적합.",
         fontsize=11.5,color='#225')

for i,(img,title,sub) in enumerate([
    ("/tmp/cmp_render/box_render/boxv2_grasp.png","box_v2 (SO 있음) — 파지 순간","발이 지면(회색) 아래로 빠짐 · 손은 박스 위"),
    ("/tmp/cmp_render/box_render/boxv11b_deep.png","box_v11b (시각 PASS) — 최저","발 접지 양호 · 그러나 SO(ES색) 없음")]):
    ax=fig.add_subplot(gs[1,i]); ax.imshow(crop(img)); ax.axis('off')
    ax.set_title(title,fontsize=13,fontweight='bold')
    ax.text(0.5,-0.06,sub,transform=ax.transAxes,ha='center',fontsize=11,color='#7a0000')
OUT="/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/literature_review/box_motion_status_grid.png"
fig.savefig(OUT,dpi=108,bbox_inches='tight',facecolor='white'); print("SAVED",OUT)
