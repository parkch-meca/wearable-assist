import bpy, os, json, sys, mathutils
argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
DATA=argv[0]; OUTDIR=argv[1]; os.makedirs(OUTDIR,exist_ok=True)
OSIM="/tmp/cmp_render/tlfb/TLFB.osim"
D=json.load(open(DATA)); geo=D['geo']; EDGE=geo['edge']; TOP=geo['top']; HALF=geo['half']; FLOOR=D['floor']; SIDES=D['sides']; N=D['n']; FR=D['frames']
def mat_from(R,p): return mathutils.Matrix(((R[0],R[1],R[2],p[0]),(R[3],R[4],R[5],p[1]),(R[6],R[7],R[8],p[2]),(0,0,0,1)))
def look_at(cl,t):
    cl=mathutils.Vector(cl); t=mathutils.Vector(t); f=(t-cl).normalized(); up=mathutils.Vector((0,1,0))
    r=f.cross(up); r=r if r.length>1e-6 else mathutils.Vector((1,0,0)); r.normalize(); u=r.cross(f).normalized()
    return mathutils.Matrix(((r.x,u.x,-f.x),(r.y,u.y,-f.y),(r.z,u.z,-f.z))).to_euler()
def smat(name,col,emis=0.35,alpha=1.0):
    mm=bpy.data.materials.new(name); mm.use_nodes=True; b=mm.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*col,1)
    if "Alpha" in b.inputs: b.inputs["Alpha"].default_value=alpha
    for en in ("Emission Color","Emission"):
        if en in b.inputs:
            try: b.inputs[en].default_value=(*[c*0.9 for c in col],1)
            except: pass
    if "Emission Strength" in b.inputs: b.inputs["Emission Strength"].default_value=emis
    if alpha<1: mm.blend_method='BLEND'
    return mm
def force_vis(o):
    for c in list(o.users_collection):
        try: c.objects.unlink(o)
        except: pass
    bpy.context.scene.collection.objects.link(o); o.hide_render=False
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections): bpy.data.collections.remove(c)
imp=getattr(bpy.ops,'import'); imp.import_opensim_model(filepath=OSIM); bpy.context.view_layer.update()
wm=smat("Bone",(0.92,0.91,0.86),0.45,1.0)
meshes={}; armR=[]; armL=[]
for o in list(bpy.data.objects):
    t=o.get('MuSkeMo_type')
    if o.type=='MESH' and t=='GEOMETRY':
        o.parent=None; o.data.materials.clear(); o.data.materials.append(wm); o.hide_render=False
        meshes[o.name]=o; sd=SIDES.get(o.name,'other')
        if sd=='R': armR.append(o)
        elif sd=='L': armL.append(o)
    elif o.type=='CURVE' or t in ('WRAP','LANDMARK','JOINT'):
        try: bpy.data.objects.remove(o,do_unlink=True)
        except: pass
for coll in bpy.data.collections:
    if any(k in coll.name.lower() for k in ['wrap','joint cent','landmark','frame','muscle']): coll.hide_render=True
Mz=mathutils.Matrix(((1,0,0,0),(0,1,0,0),(0,0,-1,0),(0,0,0,1)))
for o in armL: o.hide_render=True
mirror=[]
for o in armR:
    dup=o.copy(); dup.data=o.data.copy(); bpy.context.scene.collection.objects.link(dup); dup.hide_render=False; mirror.append((dup,o))
# ---- static scene: floor + opaque blue table + box(updated) ----
bpy.ops.mesh.primitive_plane_add(size=4.0, location=(0.3,FLOOR-0.005,0)); g=bpy.context.object
g.data.materials.append(smat("g",(0.34,0.36,0.40),0.0)); g.name="GND"; force_vis(g)
Dx=0.55; Dz=0.9; Hy=TOP-FLOOR
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(EDGE+Dx/2, FLOOR+Hy/2, 0.0)); tb=bpy.context.object; tb.scale=(Dx,Hy,Dz)
tb.data.materials.append(smat("table",(0.20,0.34,0.55),0.05,1.0)); tb.name="TABLE"; force_vis(tb)
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(EDGE+Dx/2, TOP-0.01, 0.0)); tt=bpy.context.object; tt.scale=(Dx,0.02,Dz)
tt.data.materials.append(smat("ttop",(0.30,0.46,0.68),0.2,1.0)); tt.name="TTOP"; force_vis(tt)
bpy.ops.mesh.primitive_cube_add(size=0.30, location=(0,0,0)); box=bpy.context.object
box.data.materials.append(smat("box",(0.88,0.58,0.22),0.55,1.0)); box.name="BOX"; force_vis(box)
# ---- framing over ALL frames (fixed so video doesn't jump) ----
mn=[1e9,FLOOR-0.05,-Dz/2]; mx=[-1e9,-1e9,Dz/2]
for fr in FR:
    for nm,d in fr['mx'].items():
        p=d['p']
        mn[0]=min(mn[0],p[0]); mx[0]=max(mx[0],p[0]); mx[1]=max(mx[1],p[1])
    b=fr['box']; mx[0]=max(mx[0],b[0]+HALF); mn[0]=min(mn[0],b[0]-HALF); mx[1]=max(mx[1],b[1]+HALF)
mn[0]-=0.15; mx[0]=max(mx[0],EDGE+Dx)+0.1; mx[1]+=0.15
cx=(mn[0]+mx[0])/2; cy=(mn[1]+mx[1])/2; cz=0.0
RX,RY=760,860; ortho=max(mx[1]-mn[1],(mx[0]-mn[0])*RY/RX,(mx[2]-mn[2])*RY/RX)*1.06
sc=bpy.context.scene; sc.render.engine='BLENDER_EEVEE_NEXT'; sc.render.resolution_x=RX; sc.render.resolution_y=RY
sc.render.image_settings.file_format='PNG'; sc.world.use_nodes=True
bg=sc.world.node_tree.nodes.get('Background'); bg.inputs[0].default_value=(0.11,0.12,0.15,1); bg.inputs[1].default_value=1.0
for loc,en in [((cx+3,cy+3,cz+3),5.0),((cx-2,cy+2,cz+3),4.0),((cx,cy+1,cz-3),2.8)]:
    bpy.ops.object.light_add(type='SUN',location=loc); bpy.context.object.data.energy=en
bpy.ops.object.camera_add(location=(0,0,0)); cam=bpy.context.object; sc.camera=cam
cam.data.type='ORTHO'; cam.data.ortho_scale=ortho; cam.data.sensor_fit='VERTICAL'; cam.data.clip_start=0.01; cam.data.clip_end=80
VIEWS={"side":(cx,cy+0.1,cz+7),"front":(cx+7,cy+0.1,cz)}
# ---- per-frame render ----
for fi in range(N):
    fr=FR[fi]; mxf=fr['mx']; b=fr['box']
    for nm,o in meshes.items():
        if nm in mxf: o.matrix_world=mat_from(mxf[nm]['R'],mxf[nm]['p'])
    for dup,o in mirror: dup.matrix_world=Mz@o.matrix_world
    box.location=(b[0],b[1],b[2])
    for vn,loc in VIEWS.items():
        cam.location=mathutils.Vector(loc); cam.rotation_euler=look_at(loc,(cx,cy,cz))
        sc.render.filepath=f"{OUTDIR}/{vn}_{fi:04d}.png"; bpy.ops.render.render(write_still=True)
    if fi%20==0: print(f"[frame {fi}/{N}]",flush=True)
print("BATCH_DONE")
