import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import matplotlib.image as mpimg, numpy as np, json
kf="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
fm.fontManager.addfont(kf); plt.rcParams['font.family']=fm.FontProperties(fname=kf).get_name(); plt.rcParams['axes.unicode_minus']=False
def crop(p,pad=6):
    im=mpimg.imread(p); a=(im[:,:,:3]*255).astype(int); bg=a[2,2]
    m=np.abs(a-bg).sum(2)>16; ys,xs=np.where(m)
    return im[max(0,ys.min()-pad):ys.max()+pad,max(0,xs.min()-pad):xs.max()+pad]
D=json.load(open('/tmp/cmp_render/dist_frame.json'))['diag']; C=D['contrib']
fig=plt.figure(figsize=(16,9.6)); gs=fig.add_gridspec(1,3,width_ratios=[1,1,1.75],wspace=0.05)
fig.suptitle("전척추 분산 굴곡 + semi-squat (구조변경 0) — 등 55°·간섭0·팔 3.3cm 근접, 독립검증은 여전히 과굴곡→M1 필요",
             fontsize=13.5,fontweight='bold',y=0.995,color='#1a3a6a')
for i,(p,t) in enumerate([("/tmp/cmp_render/interf/dist3_front.png","앞 — 양손 박스 옆면 대칭"),
                          ("/tmp/cmp_render/interf/dist3_side.png","옆 — 무릎 squat로 하강, 등 세움(이전보다 개선)")]):
    ax=fig.add_subplot(gs[0,i]); ax.imshow(crop(p)); ax.axis('off'); ax.set_title(t,fontsize=10,fontweight='bold')
ax=fig.add_subplot(gs[0,2]); ax.axis('off')
ax.text(0,1.0,"[전략] 부족 15~20cm를 여러 관절 분산",fontsize=12.5,fontweight='bold',color='#0a6',va='top')
ax.text(0,0.945,f"흉추 {C['thoracic_tot']:.0f}° + 요추 {C['lumbar_tot']:.0f}° + 고관절 {C['hip']:.0f}°\n"
               f"+ 무릎 squat {C['knee']:.0f}° + 발목 {C['ankle']:.0f}° + 골반 {C['pelvis_tilt']:.0f}°\n"
               "→ 무릎 쭈그림으로 수직 하강, 등을 눕히지 않음. 구조 변경 0.",fontsize=9.5,va='top')
ax.text(0,0.815,"[성과] 객관 수치 = 자연 범위 상단 ✅",fontsize=12.5,fontweight='bold',color='#0a6',va='top')
ax.text(0,0.76,f"• 등 lean(골반→T1) = {D['back_angle']:.0f}° (사용자 목표 40~55° 상단)\n"
               f"• 다리-테이블 간섭 0 (정강이 {D['shin_gap_cm']:.0f}cm 여유)\n"
               f"• 팔 부족 palm {D['palm_err_cm']:.1f}cm (거의 밀착), 좌우 대칭, 발접지",fontsize=9.5,va='top')
ax.text(0,0.65,"[한계] 독립검증은 여전히 '과굴곡'",fontsize=12.5,fontweight='bold',color='#a00',va='top')
ax.text(0,0.595,"독립검증자: 등 시각 75~85°로 읽음(수치 55°보다 과대).\n"
               "이유(객관): 어깨가 골반보다 30cm, 머리가 35cm 앞으로 돌출\n"
               "→ 박스 위로 쏠린 실루엣. lean 각도보다 '앞으로 튀어나옴'이 문제.",fontsize=9.5,va='top')
ax.text(0,0.475,"[근본] 어깨 전방돌출 = 견갑 없음",fontsize=12.5,fontweight='bold',color='#a00',va='top')
ax.text(0,0.42,"박스가 발보다 28~30cm 앞(발은 테이블에 막힘). 견갑 protraction\n"
               "없으면 어깨를 앞으로 보내려 체간을 기울일 수밖에 없음.\n"
               "분산해도 팔 3~5cm 부족 + 어깨 30cm 돌출이 남음.",fontsize=9.5,va='top')
ax.text(0,0.30,"[결론] 사용자 플랜대로 → M1",fontsize=12.5,fontweight='bold',color='#7a0000',va='top')
ax.text(0,0.245,"선택지1(분산, 구조0)로 등 55°·간섭0까지 왔으나 독립검증 통과 X.\n"
               "남은 3~5cm + 어깨 전방돌출은 M1(SC 2-DOF protraction ~8cm)이\n"
               "어깨를 독립적으로 앞으로 보내 lean 줄이고 도달도 채움.\n"
               "= 부족량 보고 완료. M1은 사용자 확인 후 진행(자동 X).",fontsize=9.5,va='top',color='#333')
ax.text(0,0.06,"정량(SO)은 견갑 무관하므로 자연 척추자세로 별도 진행 가능.",fontsize=9,fontweight='bold',color='#225',va='top')
OUT="/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/phase2_box/box_table30_distributed_grid.png"
fig.savefig(OUT,dpi=110,bbox_inches='tight',facecolor='white'); print("SAVED",OUT)
