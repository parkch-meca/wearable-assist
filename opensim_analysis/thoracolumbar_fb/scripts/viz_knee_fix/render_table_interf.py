import bpy, os, json, sys, mathutils
argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
FRAME=argv[0]; OUTBASE=argv[1]
OSIM="/tmp/cmp_render/tlfb/TLFB.osim"; RAD=0.006; D=json.load(open(FRAME)); FLOOR=-0.905
geo=D['geo']; EDGE=geo['edge']; TOP=geo['top']; GRIP=geo['grip']
def mat_from(R,p): return mathutils.Matrix(((R[0],R[1],R[2],p[0]),(R[3],R[4],R[5],p[1]),(R[6],R[7],R[8],p[2]),(0,0,0,1)))
def look_at(cl,t):
    cl=mathutils.Vector(cl); t=mathutils.Vector(t); f=(t-cl).normalized(); up=mathutils.Vector((0,1,0))
    r=f.cross(up); r=r if r.length>1e-6 else mathutils.Vector((1,0,0)); r.normalize(); u=r.cross(f).normalized()
    return mathutils.Matrix(((r.x,u.x,-f.x),(r.y,u.y,-f.y),(r.z,u.z,-f.z))).to_euler()
def smat(name,col,emis=0.4,alpha=1.0):
    m=bpy.data.materials.new(name); m.use_nodes=True; b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*col,1)
    if "Alpha" in b.inputs: b.inputs["Alpha"].default_value=alpha
    for en in ("Emission Color","Emission"):
        if en in b.inputs:
            try: b.inputs[en].default_value=(*[c*0.9 for c in col],1)
            except: pass
    if "Emission Strength" in b.inputs: b.inputs["Emission Strength"].default_value=emis
    if alpha<1: m.blend_method='BLEND'
    return m
def force_vis(o):
    for c in list(o.users_collection):
        try: c.objects.unlink(o)
        except: pass
    bpy.context.scene.collection.objects.link(o); o.hide_render=False
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections): bpy.data.collections.remove(c)
imp=getattr(bpy.ops,'import'); imp.import_opensim_model(filepath=OSIM); bpy.context.view_layer.update()
wm=smat("Bone",(0.90,0.89,0.84),0.4,0.95)
for o in list(bpy.data.objects):
    t=o.get('MuSkeMo_type')
    if o.type=='MESH' and t=='GEOMETRY':
        if o.name in D['mesh']: o.parent=None; o.matrix_world=mat_from(D['mesh'][o.name]['R'],D['mesh'][o.name]['p'])
        o.data.materials.clear(); o.data.materials.append(wm); o.hide_render=False
    elif o.type=='CURVE' or t in ('WRAP','LANDMARK','JOINT'): bpy.data.objects.remove(o,do_unlink=True)
for coll in bpy.data.collections:
    if any(k in coll.name.lower() for k in ['wrap','joint cent','landmark','frame','muscle']): coll.hide_render=True
mcoll=bpy.data.collections.new("ES"); bpy.context.scene.collection.children.link(mcoll)
neut=smat("Mn",(0.78,0.32,0.34),0.5)
for nm,md in D['muscles'].items():
    pts=md['pts']
    if len(pts)<2: continue
    cu=bpy.data.curves.new(nm,'CURVE'); cu.dimensions='3D'; sp=cu.splines.new('POLY'); sp.points.add(len(pts)-1)
    for i,(x,y,z) in enumerate(pts): sp.points[i].co=(x,y,z,1)
    cu.bevel_depth=RAD; cu.use_fill_caps=True
    ob=bpy.data.objects.new(nm,cu); mcoll.objects.link(ob); ob.data.materials.append(neut)
# ground
bpy.ops.mesh.primitive_plane_add(size=3.0, location=(0.4,FLOOR,0)); g=bpy.context.object; g.data.materials.append(smat("g",(0.26,0.28,0.32),0.0)); g.name="GND"; force_vis(g)
# TABLE slab: x[EDGE,EDGE+0.6], y[FLOOR,TOP], z +-0.35
import mathutils as mu
tdepth=0.6; tw=0.35; tht=TOP-FLOOR
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(EDGE+tdepth/2, FLOOR+tht/2, 0.0))
tb=bpy.context.object; tb.scale=(tdepth/2, tht/2, tw); tb.data.materials.append(smat("table",(0.50,0.52,0.60),0.1)); tb.name="TABLE"; force_vis(tb)
# BOX on table at grip
bpy.ops.mesh.primitive_cube_add(size=0.30, location=(GRIP[0], TOP+0.15, 0.0))
bx=bpy.context.object; bx.data.materials.append(smat("box",(0.85,0.55,0.20),0.6)); bx.name="BOX"; force_vis(bx)
# edge marker line (where legs must not pass): a thin red vertical plane at x=EDGE (front face of table) - skip, table front face shows it
mn=[1e9]*3;mx=[-1e9]*3
for o in bpy.data.objects:
    if o.type in ('MESH','CURVE') and not o.hide_render and o.name!="GND":
        for v in o.bound_box:
            wv=o.matrix_world@mathutils.Vector(v)
            for i in range(3): mn[i]=min(mn[i],wv[i]); mx[i]=max(mx[i],wv[i])
cx=(mn[0]+mx[0])/2;cy=(mn[1]+mx[1])/2;cz=(mn[2]+mx[2])/2
RX,RY=1000,1000; ortho=max(mx[1]-mn[1],(mx[0]-mn[0])*RY/RX)*1.1
sc=bpy.context.scene; sc.render.engine='BLENDER_EEVEE_NEXT'; sc.render.resolution_x=RX; sc.render.resolution_y=RY
sc.render.image_settings.file_format='PNG'; sc.world.use_nodes=True
bg=sc.world.node_tree.nodes.get('Background'); bg.inputs[0].default_value=(0.09,0.10,0.12,1); bg.inputs[1].default_value=1.0
for loc,en in [((cx+2,cy+2,cz+3),5.0),((cx-2,cy+1,cz+3),4.0),((cx,cy-1,cz-3),2.8)]:
    bpy.ops.object.light_add(type='SUN',location=loc); bpy.context.object.data.energy=en
bpy.ops.object.camera_add(location=(0,0,0)); cam=bpy.context.object; sc.camera=cam
cam.data.type='ORTHO'; cam.data.ortho_scale=ortho; cam.data.sensor_fit='VERTICAL'; cam.data.clip_start=0.01; cam.data.clip_end=60
for vn,loc in {"side":(cx,cy,cz+6),"front":(cx+6,cy,cz)}.items():
    cam.location=mathutils.Vector(loc); cam.rotation_euler=look_at(loc,(cx,cy,cz))
    sc.render.filepath=f"{OUTBASE}_{vn}.png"; bpy.ops.render.render(write_still=True); print("[render]",vn)
print("INTERF_DONE")
