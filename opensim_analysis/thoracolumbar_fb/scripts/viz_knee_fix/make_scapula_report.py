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
fig=plt.figure(figsize=(16,9.6)); gs=fig.add_gridspec(1,3,width_ratios=[1,1,1.85],wspace=0.05)
fig.suptitle("견갑골 자유도 조사 — 방법·정량영향·권장경로 (실제 수정 X, 사용자 결정 대기)",
             fontsize=14.5,fontweight='bold',y=0.995,color='#1a3a6a')
for i,(p,t) in enumerate([("/tmp/cmp_render/interf/vproto_side.png","viz-전용 시제 옆 — 자연 체간(41°)이나\n필요 shift 20cm→어깨서 팔 분리(착시)"),
                          ("/tmp/cmp_render/interf/vproto_front.png","viz-전용 시제 앞 — 팔이 어깨서 분리")]):
    ax=fig.add_subplot(gs[0,i]); ax.imshow(crop(p)); ax.axis('off'); ax.set_title(t,fontsize=9.5,fontweight='bold')
ax=fig.add_subplot(gs[0,2]); ax.axis('off')
ax.text(0,1.0,"[구조] 견갑 = 이미 있으나 용접(고정)",fontsize=12.5,fontweight='bold',color='#a00',va='top')
ax.text(0,0.945,"scapula_R·clavicle_R body 존재 → 흉골-쇄골·쇄골-견갑 = WeldJoint.\n"
               "원본 배포판 설계(우리 수정 아님). 자유 DOF는 어깨(GH) 3개뿐.",fontsize=9.3,va='top')
ax.text(0,0.855,"[정량영향] ES는 견갑과 무관 ✅",fontsize=12.5,fontweight='bold',color='#0a6',va='top')
ax.text(0,0.80,"견갑 부착근 74개=전부 어깨근(deltoid/trap/serratus/rotator cuff).\n"
               "ES(iliocostalis/longissimus/multifidus)는 견갑 부착 0개.\n"
               "→ 견갑 DOF가 ES line-of-action 직접 변경 X. ES 변화 <5%p 예상\n"
               "  (Cholewicki 1996). 단 0 아님 → Phase 1a regression 필요.",fontsize=9.3,va='top')
ax.text(0,0.665,"[난이도 실측] 팔 부족 15~20cm (수직)",fontsize=12.5,fontweight='bold',color='#a00',va='top')
ax.text(0,0.61,"자연 자세서 어깨가 파지점보다 15~20cm 높음.\n"
               "• 흉추 최대굴곡(기존 DOF): 어깨 −6cm뿐 → 부족(14.7cm 잔여)\n"
               "• 생리적 견갑 protraction: ~4~8cm → 혼자 못 닫음\n"
               "= 어떤 단일 수단보다 부족량이 큼.",fontsize=9.3,va='top')
ax.text(0,0.475,"[경로 비교]",fontsize=12.5,fontweight='bold',color='#225',va='top')
ax.text(0,0.42,"❌ viz-전용 강체이동: 필요 shift 커서 어깨 분리 착시(좌측 실증)\n"
               "△ M1 SC 2-DOF: 최소수정 ~8cm 전방, regression 필요(ES<5%p)\n"
               "○ M3 Seth ScapTho 4-DOF: 수직 depression 포함 최고충실, 2~3일+큰 regression\n"
               "○ 기존 전척추 DOF 최대활용: 구조변경 0, 회귀위험 0, 자세는 깊음",fontsize=9.3,va='top')
ax.text(0,0.265,"[핵심] 정량 vs 시각 분리",fontsize=12.5,fontweight='bold',color='#0a6',va='top')
ax.text(0,0.215,"ES suit 정량(SO)=척추 근육→견갑 불필요. 자연 척추자세로 정확.\n"
               "견갑 문제는 '손이 박스에 닿아 보이는' 시각화에서만 발생.",fontsize=9.3,va='top')
ax.text(0,0.12,"[권장] 단계적",fontsize=12.5,fontweight='bold',color='#7a0000',va='top')
ax.text(0,0.07,"1순위 기존 전척추 DOF+semi-squat(구조0) → 2순위 M1 보완(regression)\n"
               "→ M3는 논문급 필요시만. viz-전용 비권장. 실제수정은 결정 후.",fontsize=9.3,va='top',color='#333')
OUT="/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/phase2_box/scapula_dof_investigation_grid.png"
fig.savefig(OUT,dpi=110,bbox_inches='tight',facecolor='white'); print("SAVED",OUT)
