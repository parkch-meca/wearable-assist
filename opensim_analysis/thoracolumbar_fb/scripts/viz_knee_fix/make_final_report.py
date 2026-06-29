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
fig=plt.figure(figsize=(16,9.5)); gs=fig.add_gridspec(2,3,height_ratios=[1.0,1.05],hspace=0.16,wspace=0.08)
fig.suptitle("박스 양손 파지 — palm 방향 해결(진전) + 자연 팔자세 auto-IK 한계 (정직 보고)",fontsize=16.5,fontweight='bold',y=0.99)
imgs=[("/tmp/cmp_render/interf/palm50_front.png","palm50 앞 — 손바닥 향함(진전)\n그러나 한 팔 어색(관대한 PASS였음)"),
      ("/tmp/cmp_render/interf/wrap50_front.png","감싸기 앞 — 양손 akimbo\n(엄격 검증이 양손 각각 FAIL)"),
      ("/tmp/cmp_render/interf/wrapF_front.png","앞코너 앞 — 여전히 양손 akimbo\n팔꿈치 벌어짐·손 윗중앙 모임")]
for i,(p,t) in enumerate(imgs):
    ax=fig.add_subplot(gs[0,i]); ax.imshow(crop(p)); ax.axis('off'); ax.set_title(t,fontsize=10.5,fontweight='bold')
ax=fig.add_subplot(gs[1,:]); ax.axis('off')
ax.text(0,1.0,"[진전] 손목 시각화 해제 = palm 방향 해결(5개월 근본원인)",fontsize=13.5,fontweight='bold',color='#1a7',va='top')
ax.text(0,0.91,"• palm normal 부호 실측 수정(엄지/새끼/중지 frame) → 손바닥 R(−Z)/L(+Z) 박스 향함, 손가락 아래로(−Y). 손등→손바닥 해결. .osim 불변(정량0).",fontsize=11,va='top',color='#225')
ax.text(0,0.78,"[검증 구조 작동·강화] 사용자 지적 반영해 '양손 각각' 판정 추가 → 이전 관대한 PASS(palm50) 무효화, 양손 akimbo 포착",fontsize=13.5,fontweight='bold',color='#a00',va='top')
ax.text(0,0.69,"• 독립 검증 ~10라운드: 엄지면→박스뜸→akimbo→위접근→off-box→손등→(보강)양손akimbo. 검증자가 매번 먼저 잡음. 억지 PASS 없음.",fontsize=11,va='top',color='#225')
ax.text(0,0.57,"[auto-IK 한계 — 자연 팔자세 양산 실패]",fontsize=13.5,fontweight='bold',color='#a00',va='top')
ax.text(0,0.48,"• 그립 변형 다 시도(중앙옆면·앞코너·어깨 박스위·어깨 뒤위·손끝 아래 타겟) → 매번 팔꿈치 akimbo + 과도 stoop.\n"
               "• 원인: 테이블 뒤에서 박스 옆면을 손바닥 안쪽으로 누르려면 어깨폭(±0.17)에서 팔꿈치가 벌어져야 함(기하적). auto-IK는 제약(손위치+손바닥방향)만 만족, 팔 미관은 무시.",fontsize=11,va='top',color='#333')
ax.text(0,0.30,"[정직한 판단] auto-IK 추가 반복은 수렴 가능성 낮음 → 여기서 멈추고 방향 결정 요청 (억지로 더 안 돌림).",fontsize=12,fontweight='bold',color='#7a0000',va='top')
ax.text(0,0.20,"[옵션]",fontsize=12.5,fontweight='bold',va='top')
ax.text(0,0.12,"(C) ★권고: 파지 클로즈업 없이 들기 동작만 — 손이 박스 근처, 손가락 안 따짐 (v11b 선례; 영상 메시지는 ES 활성도·슈트효과이지 그립 아님).\n"
               "(B) 팔을 수동 애니메이션 포즈(자동 IK 아닌 사람이 자연 각도 지정) — 노동 크나 자연스러움 확보.\n"
               "(E) 박스 시나리오 재고(박스 더 좁게/추상 그립) 또는 박스 동작 보류하고 stoop·squat 2종으로 마무리.",fontsize=10.8,va='top',color='#225')
OUT="/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/literature_review/box_grasp_autoIK_limit_report.png"
fig.savefig(OUT,dpi=108,bbox_inches='tight',facecolor='white'); print("SAVED",OUT)
