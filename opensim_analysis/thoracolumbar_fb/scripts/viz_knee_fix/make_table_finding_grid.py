import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import matplotlib.image as mpimg, numpy as np
kf="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
fm.fontManager.addfont(kf); plt.rcParams['font.family']=fm.FontProperties(fname=kf).get_name(); plt.rcParams['axes.unicode_minus']=False
def crop(p,pad=10):
    im=mpimg.imread(p); a=(im[:,:,:3]*255).astype(int); bg=a[2,2]
    m=np.abs(a-bg).sum(2)>22; ys,xs=np.where(m)
    return im[max(0,ys.min()-pad):ys.max()+pad, max(0,xs.min()-pad):xs.max()+pad]
fig=plt.figure(figsize=(15,9)); gs=fig.add_gridspec(1,3,width_ratios=[1,1,1.5],wspace=0.08)
fig.suptitle("테이블 박스 들기 — 동작 사실 확인 (재설계 검토)",fontsize=19,fontweight='bold',y=0.99)
for i,(p,t) in enumerate([("/tmp/cmp_render/table_pose/table_side.png","옆 (SIDE) — 전방 reach"),
                          ("/tmp/cmp_render/table_pose/table_front.png","앞 (FRONT)")]):
    ax=fig.add_subplot(gs[0,i]); ax.imshow(crop(p)); ax.axis('off'); ax.set_title(t,fontsize=13,fontweight='bold')
ax=fig.add_subplot(gs[0,2]); ax.axis('off')
txt=(
"■ [0] 박스 질량 = 20 kg (양손 각 100 N) — 기존 box_v2와 동일.\n"
"   테이블 시나리오 질량은 CHEOL HOON님 결정 (kinematic 검증은 질량 무관).\n\n"
"■ 테이블의 효과 (확인됨):\n"
"  ✅ 발 접지 해결 — 박스를 올리니 발이 지면에 유지(매몰 0cm).\n"
"     → 바닥 박스의 '발 23cm 지하' 문제는 테이블로 해소.\n\n"
"■ 그러나 새 제약 (모델 어깨 한계, 사실):\n"
"  ⚠️ OpenSim 어깨에 elevation 특이점 — 팔을 앞으로 뻗으면\n"
"     손이 항상 어깨(가슴) 높이 이상에 옵니다 (앞으로+아래로 reach 불가).\n"
"  → 균형 잡힌 발-접지 파지는 손이 가슴 높이·팔길이 앞(전방 0.6 m)에 위치\n"
"     = 테이블 약 105 cm (높은 작업대/카운터)에서 성립. 50 cm 아님.\n"
"  → 50 cm 테이블은 어깨를 낮추려 상체를 깊이 숙여야 함(바닥문제 재접근).\n\n"
"■ 균형/접지 (105 cm 카운터 자세):\n"
"  ✅ 발 접지(-0.905)  ✅ COM 발 지지면 내  ✅ 무릎 적당(40°)\n"
"  → 발·균형은 OK, 단 '낮은 테이블'이 아니라 '높은 카운터 reach'.\n\n"
"■ 박스/테이블 렌더: 위치 산출됨(박스중심 0.63,0.31 / 테이블 106cm)\n"
"   단 카메라 프레이밍에서 박스 표시 디버깅 필요(방향 확정 후).\n\n"
"■ 분기: 손 박스 접촉은 '높은 카운터(~105cm)'에서만 깨끗 →\n"
"   A) 105cm 카운터/작업대 시나리오로 진행(발접지+균형+접촉 OK, 산업현장 현실적)\n"
"   B) 50cm 고수 → 깊은 숙임(바닥문제 재현) 감수\n"
"   C) 박스 보류(closure 존중)\n"
"   ※ 새 모션 무한 시도 X — 방향 결정 요청."
)
ax.text(0.0,0.99,txt,va='top',ha='left',fontsize=11.3,family='monospace' if False else None)
OUT="/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/literature_review/table_box_finding_grid.png"
fig.savefig(OUT,dpi=108,bbox_inches='tight',facecolor='white'); print("SAVED",OUT)
