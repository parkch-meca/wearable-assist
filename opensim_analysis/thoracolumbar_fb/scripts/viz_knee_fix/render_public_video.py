"""Public video render: side only, OFF/ON, green->red 부담 색, opaque bones.
per-frame knee fix. Visualization only. Usage: blender -b --python this -- <frames_dir> <out_dir>"""
import bpy, os, json, glob, sys, mathutils
argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
FRAMES_DIR=argv[0] if argv else "/tmp/cmp_render/vframes"
OUT=argv[1] if len(argv)>1 else "/tmp/cmp_render/pub_vout"
os.makedirs(OUT,exist_ok=True)
OSIM="/tmp/cmp_render/tlfb/TLFB.osim"
RAD=0.006; PX,PY=720,940
VMAX=0.28; AMIN=0.13
GYR=[(0.00,0.10,0.66,0.18),(0.40,0.55,0.80,0.10),(0.58,0.96,0.86,0.10),(0.78,0.97,0.45,0.05),(1.00,0.88,0.04,0.04)]
def gyr(x):
    x=max(0.,min(1.,x))
    for i in range(len(GYR)-1):
        t0,r0,g0,b0=GYR[i]; t1,r1,g1,b1=GYR[i+1]
        if x<=t1:
            f=(x-t0)/(t1-t0) if t1>t0 else 0; return (r0+(r1-r0)*f,g0+(g1-g0)*f,b0+(b1-b0)*f)
    return GYR[-1][1:]
def colof(a): n=max(0.,min(1.,(a-AMIN)/(VMAX-AMIN))); return gyr(n),n
def mat_from(R,p):
    return mathutils.Matrix(((R[0],R[1],R[2],p[0]),(R[3],R[4],R[5],p[1]),(R[6],R[7],R[8],p[2]),(0,0,0,1)))
def look_at(cl,t):
    cl=mathutils.Vector(cl); t=mathutils.Vector(t); f=(t-cl).normalized(); up=mathutils.Vector((0,1,0))
    r=f.cross(up); r=r if r.length>1e-6 else mathutils.Vector((1,0,0)); r.normalize(); u=r.cross(f).normalized()
    return mathutils.Matrix(((r.x,u.x,-f.x),(r.y,u.y,-f.y),(r.z,u.z,-f.z))).to_euler()
def white_mat():
    m=bpy.data.materials.get("BoneWhite")
    if m: return m
    m=bpy.data.materials.new("BoneWhite"); m.use_nodes=True
    b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(0.92,0.91,0.86,1)
    if "Roughness" in b.inputs: b.inputs["Roughness"].default_value=0.55
    if "Alpha" in b.inputs: b.inputs["Alpha"].default_value=0.88
    for en in ("Emission Color","Emission"):
        if en in b.inputs:
            try: b.inputs[en].default_value=(0.85,0.84,0.78,1)
            except: pass
    if "Emission Strength" in b.inputs: b.inputs["Emission Strength"].default_value=0.4
    m.blend_method='BLEND'
    return m

files=sorted(glob.glob(os.path.join(FRAMES_DIR,"frame_*.json")), key=lambda p:float(os.path.basename(p)[6:-5]))
frames=[json.load(open(f)) for f in files]
print("[frames]",len(frames))

bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections): bpy.data.collections.remove(c)
imp=getattr(bpy.ops,'import'); imp.import_opensim_model(filepath=OSIM)
bpy.context.view_layer.update()
wm=white_mat(); bone_objs={}
for o in list(bpy.data.objects):
    t=o.get('MuSkeMo_type')
    if o.type=='MESH' and t=='GEOMETRY':
        o.data.materials.clear(); o.data.materials.append(wm); o.hide_render=False
        if o.parent: o.parent=None
        bone_objs[o.name]=o
    elif o.type=='CURVE' or t in ('WRAP','LANDMARK','JOINT'):
        bpy.data.objects.remove(o, do_unlink=True)
for coll in bpy.data.collections:
    if any(k in coll.name.lower() for k in ['wrap','joint cent','landmark','frame','muscle']):
        coll.hide_render=True
musc_names=list(frames[0]['muscles'].keys())
musc_mats={nm:bpy.data.materials.new("m_"+nm) for nm in musc_names}
for mm in musc_mats.values(): mm.use_nodes=True
mcoll=bpy.data.collections.new("ES"); bpy.context.scene.collection.children.link(mcoll)

# global bbox
mn=[1e9]*3; mx=[-1e9]*3
for fr in frames:
    for mp in fr['muscles'].values():
        for x,y,z in mp['pts']:
            mn[0]=min(mn[0],x);mn[1]=min(mn[1],y);mn[2]=min(mn[2],z);mx[0]=max(mx[0],x);mx[1]=max(mx[1],y);mx[2]=max(mx[2],z)
    for mxf in fr['mesh'].values():
        p=mxf['p']
        for i in range(3): mn[i]=min(mn[i],p[i]); mx[i]=max(mx[i],p[i])
for i in range(3): mn[i]-=0.10; mx[i]+=0.10
cx=(mn[0]+mx[0])/2; cy=(mn[1]+mx[1])/2; cz=(mn[2]+mx[2])/2
xext=mx[0]-mn[0]; yext=mx[1]-mn[1]
ortho=max(yext, xext*PY/PX)*1.02
sc=bpy.context.scene
sc.render.engine='BLENDER_EEVEE_NEXT'; sc.render.resolution_x=PX; sc.render.resolution_y=PY
sc.render.image_settings.file_format='PNG'; sc.world.use_nodes=True
bg=sc.world.node_tree.nodes.get('Background')
if bg: bg.inputs[0].default_value=(0.05,0.055,0.07,1); bg.inputs[1].default_value=1.0
for loc,en in [((cx+2,cy+2,cz+3),5.0),((cx-2,cy+1,cz+3),4.0),((cx,cy-1,cz-3),2.8)]:
    bpy.ops.object.light_add(type='SUN',location=loc); bpy.context.object.data.energy=en
bpy.ops.object.camera_add(location=(0,0,0)); cam=bpy.context.object; sc.camera=cam
cam.data.type='ORTHO'; cam.data.ortho_scale=ortho; cam.data.sensor_fit='VERTICAL'
cam.data.clip_start=0.01; cam.data.clip_end=60
SIDE=(cx,cy,cz+6)
cam.location=mathutils.Vector(SIDE); cam.rotation_euler=look_at(SIDE,(cx,cy,cz))

cur=[]
def build(fr):
    global cur
    for ob in cur: bpy.data.objects.remove(ob, do_unlink=True)
    cur=[]
    for nm,mp in fr['muscles'].items():
        pts=mp['pts']
        if len(pts)<2: continue
        cu=bpy.data.curves.new(nm,'CURVE'); cu.dimensions='3D'
        sp=cu.splines.new('POLY'); sp.points.add(len(pts)-1)
        for i,(x,y,z) in enumerate(pts): sp.points[i].co=(x,y,z,1)
        cu.bevel_depth=RAD; cu.use_fill_caps=True
        ob=bpy.data.objects.new(nm,cu); mcoll.objects.link(ob); ob.data.materials.append(musc_mats[nm]); cur.append(ob)
def recolor(fr,cond):
    for nm,mp in fr['muscles'].items():
        mm=musc_mats.get(nm)
        if mm is None: continue
        col,n=colof(mp[cond]); b=mm.node_tree.nodes.get("Principled BSDF")
        b.inputs["Base Color"].default_value=(col[0],col[1],col[2],1)
        for en in ("Emission Color","Emission"):
            if en in b.inputs:
                try: b.inputs[en].default_value=(col[0],col[1],col[2],1)
                except: pass
        if "Emission Strength" in b.inputs: b.inputs["Emission Strength"].default_value=0.2+1.4*n
meta=[]
for fi,fr in enumerate(frames):
    for nm,mxf in fr['mesh'].items():
        if nm in bone_objs: bone_objs[nm].matrix_world=mat_from(mxf['R'],mxf['p'])
    build(fr)
    pairs=[(v['off'],v['on']) for v in fr['muscles'].values()]; pk=max(pairs,key=lambda ab:ab[0])
    red=100*(pk[0]-pk[1])/pk[0] if pk[0]>1e-6 else 0
    meta.append({'t':fr['t'],'peak_off':pk[0],'peak_on':pk[1],'peak_red':red})
    for cond in ['off','on']:
        recolor(fr,cond)
        sc.render.filepath=os.path.join(OUT,f"f{fi:04d}_{cond}_side.png")
        bpy.ops.render.render(write_still=True)
    if fi%15==0: print("[frame]",fi,"t=",round(fr['t'],2))
json.dump(meta, open(os.path.join(OUT,"meta.json"),"w"))
print("PUB_VIDEO_RENDER_DONE",len(frames))
