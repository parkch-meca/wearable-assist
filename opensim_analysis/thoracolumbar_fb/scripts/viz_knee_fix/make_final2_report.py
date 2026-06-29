import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import matplotlib.image as mpimg, numpy as np
kf="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
fm.fontManager.addfont(kf); plt.rcParams['font.family']=fm.FontProperties(fname=kf).get_name(); plt.rcParams['axes.unicode_minus']=False
def crop(p,pad=6):
    im=mpimg.imread(p); a=(im[:,:,:3]*255).astype(int); bg=a[2,2]
    m=np.abs(a-bg).sum(2)>16; ys,xs=np.where(m)
    return im[max(0,ys.min()-pad):ys.max()+pad,max(0,xs.min()-pad):xs.max()+pad]
fig=plt.figure(figsize=(15,9)); gs=fig.add_gridspec(1,3,width_ratios=[1,1,1.6],wspace=0.07)
fig.suptitle("박스 들기 모션 동작검증 — 한 손 splay (미러의 방향 한계 발견) · 정직 보고",fontsize=15.5,fontweight='bold',y=0.99)
for i,(p,t) in enumerate([("/tmp/cmp_render/interf/liftgrasp_front.png","파지 앞 — 왼손 박스, 오른손 허공 splay"),
                          ("/tmp/cmp_render/interf/liftpeak_front.png","들기 앞 — 같은 비대칭")]):
    ax=fig.add_subplot(gs[0,i]); ax.imshow(crop(p)); ax.axis('off'); ax.set_title(t,fontsize=10.5,fontweight='bold')
ax=fig.add_subplot(gs[0,2]); ax.axis('off')
ax.text(0,1.0,"[검증이 잡은 것] 모션 grasp/lift 두 순간 모두 한 손 허공 splay (독립검증 FAIL)",fontsize=12.5,fontweight='bold',color='#a00',va='top')
ax.text(0,0.91,"이전 미러 PASS는 손 '위치' 대칭만 봐서, 손 '방향' 틀어짐을 놓쳤음. 모션+박스 렌더에서 드러남.",fontsize=10.8,va='top')
ax.text(0,0.80,"[근본 원인 — 모델 한계 확정]",fontsize=13,fontweight='bold',color='#a00',va='top')
ax.text(0,0.71,"• 미러는 손 '위치'만 맞춤(1.1cm). 모델의 좌우 팔 관절 frame이 완벽한 거울이 아님\n"
               "  → 같은 관절값이 위치는 대칭이나 한쪽 손바닥이 박스 반대로 향함(splay).\n"
               "• 왼손목 3DOF만 재교정 시도 → 손바닥 +Z 성분 0.28까지만(불충분). 어깨/팔꿈치 미러값에 묶여 손목만으론 못 돌림.",fontsize=10.6,va='top',color='#333')
ax.text(0,0.52,"[두 자동 방법 — 각각 1개 결함 (양립 불가)]",fontsize=12.5,fontweight='bold',color='#a00',va='top')
rows=[["방법","결과","결함"],
 ["독립 팔 IK","양 손바닥 박스 향함","팔꿈치 akimbo(테이블뒤 기하)"],
 ["미러(오른→왼)","대칭·akimbo 없음","한 손바닥 방향 틀림(L/R 비대칭 frame)"]]
tb=ax.table(cellText=rows,bbox=[0,0.30,1.0,0.18]); tb.auto_set_font_size(False); tb.set_fontsize(9.5)
for (r,c),cell in tb.get_celld().items():
    if r==0: cell.set_facecolor('#e8e8e8'); cell.set_text_props(fontweight='bold')
    else: cell.set_facecolor('#fbe9e7')
    cell.set_edgecolor('#aaa')
ax.text(0,0.24,"★ 생성/검증 분리 ~13라운드: 검증자가 매번 먼저 잡음(splay·akimbo·손등·박스뜸…). 억지 PASS 0.",fontsize=10.6,fontweight='bold',color='#a00',va='top')
ax.text(0,0.15,"[정직 판단] 자동 IK·미러로 깨끗한 양손 파지 클로즈업 = 이 모델·시나리오에서 불가(반복 수렴 X). 멈춤.",fontsize=11,fontweight='bold',color='#7a0000',va='top')
ax.text(0,0.07,"[옵션] (B)팔 수동 애니포즈(사람이 양팔 직접) — 자동 불가한 자연 그립 유일한 길.\n"
               "      (C)파지 클로즈업 없이 들기 동작만 — 손 박스 근처, 박스 손따라 상승. 영상 메시지=ES/슈트효과(그립 아님).\n"
               "      모션·SO·동영상 파이프라인은 준비됨(table_box_lift_v1.mot). 그립 표현만 (B)/(C) 결정.",fontsize=10.4,va='top',color='#225')
OUT="/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/literature_review/box_lift_motion_verify_report.png"
fig.savefig(OUT,dpi=108,bbox_inches='tight',facecolor='white'); print("SAVED",OUT)
