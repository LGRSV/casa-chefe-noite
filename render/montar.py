"""Monta a cena no Blender e renderiza (Cycles CPU + OpenImageDenoise + AgX).
Uso: blender -b -P render/montar.py -- MODO [amostras] [escala] [pasta_saida]
  MODO: main  -> base.png, <comodo>.png (so a luz do comodo), noite.png, pontos.json  (2400x1500)
        giro  -> giro_01..12.jpg (1600x1000, ~24 graus em volta, luzes tipicas acesas)
        teste -> um quadro rapido (base + comodos) para conferir
Os comodos usam LIGHT GROUPS: uma unica renderizacao gera a base e uma passada por comodo."""
import bpy, sys, os, json, math, time, glob
from mathutils import Vector, Matrix
import bmesh
from bpy_extras.object_utils import world_to_camera_view

AQUI = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
MODO = args[0] if args else 'teste'
AMOSTRAS = int(args[1]) if len(args) > 1 else 16
ESCALA = float(args[2]) if len(args) > 2 else 0.5
SAIDA = args[3] if len(args) > 3 else os.path.join(AQUI, 'saida')
os.makedirs(SAIDA, exist_ok=True)
CENA = json.load(open(os.path.join(AQUI, 'cena.json'), encoding='utf-8'))
T0 = time.time()

def b3(p):  # three (x,y,z) -> blender (x,-z,y)
    return Vector((p[0], -p[2], p[1]))

def hex_lin(h):  # cor sRGB do three (ja linear no motor: Color.getHex devolve sRGB)
    r, g, b = ((h >> 16) & 255) / 255, ((h >> 8) & 255) / 255, (h & 255) / 255
    f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (f(r), f(g), f(b))

# ---------------------------------------------------------------- cena limpa + import
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(AQUI, 'casa.glb'))
sc = bpy.context.scene
for o in list(bpy.data.objects):
    if o.type in ('CAMERA', 'LIGHT'):
        bpy.data.objects.remove(o)

ROOMS = CENA['rooms']
def room_of_three(x, z):
    best, bd = None, 1e9
    for r in ROOMS:
        x0, z0, x1, z1 = r['box']
        d = math.hypot(max(x0 - x, 0, x - x1), max(z0 - z, 0, z - z1))
        if d < bd: best, bd = r['id'], d
    return best

def room_of_obj(o):
    c = sum((o.matrix_world @ Vector(v) for v in o.bound_box), Vector()) / 8
    return room_of_three(c.x, -c.y)  # blender (x,y,z) -> three (x, z=-y)

# ---------------------------------------------------------------- materiais
def principled(m):
    return m.node_tree.nodes.get('Principled BSDF') if m.use_nodes and m.node_tree else None

def lum(c): return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]

emissivos = []   # (obj, material, strength_original, grupo)
mat_tipo = {}
for m in bpy.data.materials:
    p = principled(m)
    if not p:   # unlit do three (halo/tampa): vira transparente
        nt_ = m.node_tree; nt_.nodes.clear()
        tb = nt_.nodes.new('ShaderNodeBsdfTransparent'); mo = nt_.nodes.new('ShaderNodeOutputMaterial'); nt_.links.new(tb.outputs[0], mo.inputs[0])
        mat_tipo[m.name] = 'invisivel'; continue
    m.blend_method = 'OPAQUE' if hasattr(m, 'blend_method') else None
    col = p.inputs['Base Color'].default_value
    alpha = p.inputs['Alpha'].default_value
    rough = p.inputs['Roughness'].default_value
    metal = p.inputs['Metallic'].default_value
    emi = p.inputs['Emission Strength'].default_value
    if m.name == 'agua':
        tipo = 'agua'
        p.inputs['Base Color'].default_value = (0.02, 0.45, 0.55, 1)
        p.inputs['Alpha'].default_value = 1.0
        p.inputs['Roughness'].default_value = 0.08
        p.inputs['Specular IOR Level'].default_value = 0.8
        p.inputs['Emission Color'].default_value = (0.05, 0.85, 0.9, 1)
        p.inputs['Emission Strength'].default_value = 0.0   # liga so no grupo da piscina (ver abaixo)
    elif alpha < 0.98:
        tipo = 'vidro'
        p.inputs['Alpha'].default_value = 1.0
        p.inputs['Transmission Weight'].default_value = 1.0
        p.inputs['Roughness'].default_value = 0.03
        p.inputs['IOR'].default_value = 1.0   # plano fino: sem refracao
        c = p.inputs['Base Color'].default_value
        p.inputs['Base Color'].default_value = (0.82 + c[0] * .1, 0.95, 0.9, 1)  # leve tom verde
    elif emi > 0.01:
        tipo = 'luz'
    elif metal > 0.5:
        tipo = 'metal'
        p.inputs['Roughness'].default_value = max(rough, 0.22)
    elif lum(col) < 0.03:
        tipo = 'preto'
        p.inputs['Roughness'].default_value = 0.55
        p.inputs['Specular IOR Level'].default_value = 0.3
    elif lum(col) > 0.6 and max(col[:3]) - min(col[:3]) < 0.12:
        tipo = 'parede'
        p.inputs['Roughness'].default_value = max(rough, 0.82)
    elif col[0] > col[2] * 1.5 and lum(col) < 0.45:
        tipo = 'madeira'
        p.inputs['Roughness'].default_value = min(max(rough, 0.45), 0.6)
    else:
        tipo = 'outro'
        p.inputs['Roughness'].default_value = max(rough, 0.4)
    mat_tipo[m.name] = tipo

# ---------------------------------------------------------------- objetos: lightgroups, bevel
mesh_objs = [o for o in bpy.data.objects if o.type == 'MESH']
for o in mesh_objs:
    mats = [s.material for s in o.material_slots if s.material]
    tipos = [mat_tipo.get(m.name) for m in mats]
    rid = room_of_obj(o)
    # emissivos: copia propria do material para poder apagar por comodo
    for i, s in enumerate(o.material_slots):
        m = s.material
        if m and mat_tipo.get(m.name) == 'luz':
            m2 = m.copy(); s.material = m2
            p = principled(m2)
            emissivos.append((o, p, p.inputs['Emission Strength'].default_value, rid))
            o.lightgroup = rid
            mat_tipo[m2.name] = 'luz'
        if m and mat_tipo.get(m.name) == 'agua':
            o.lightgroup = 'piscina'
            principled(m).inputs['Emission Strength'].default_value = 0.12
    if any(t in ('agua', 'vidro') for t in tipos): o.visible_shadow = False   # vidro nao bloqueia a luz (Cycles nao refrata luz direta)
    # bevel (so em solidos): remove doubles + bevel fino
    if any(t in ('agua', 'vidro') for t in tipos) or not o.data.polygons: continue
    dims = o.dimensions
    mn = min(d for d in dims if d > 1e-4) if any(d > 1e-4 for d in dims) else 0
    if mn < 0.025: continue
    me = o.data
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bm.to_mesh(me); bm.free()
    for poly in me.polygons: poly.use_smooth = False
    bpy.context.view_layer.objects.active = o
    try: bpy.ops.mesh.customdata_custom_splitnormals_clear()
    except Exception: pass
    md = o.modifiers.new('bevel', 'BEVEL')
    md.width = min(0.008, mn * 0.18); md.segments = 2; md.limit_method = 'ANGLE'; md.angle_limit = math.radians(35); md.harden_normals = False

# ---------------------------------------------------------------- luzes
GRUPOS = ['estudio'] + [r['id'] for r in ROOMS]
vl = bpy.context.view_layer
for g in GRUPOS:
    vl.lightgroups.add(name=g)
K = 2700
QUENTE = (1.0, 0.66, 0.36)
luzes = {}  # grupo -> [obj]
def add_point(room, pos3, power, color, radius=0.12, nome=None):
    d = bpy.data.lights.new(nome or ('luz_' + room), 'POINT')
    d.energy = power; d.color = color; d.shadow_soft_size = radius
    o = bpy.data.objects.new(d.name, d); sc.collection.objects.link(o)
    o.location = b3(pos3); o.lightgroup = room
    luzes.setdefault(room, []).append(o)
    return o
FATOR = 18.0   # candela do motor -> watts do Blender (calibrado no teste)
tem = {}
for L in CENA['lights']:
    tem.setdefault(L['room'], []).append(L)
    sub = L['room'] == 'piscina'
    add_point(L['room'], L['pos'], L['i'] * FATOR * (1.6 if sub else 1), (0.1, 0.9, 0.95) if sub else QUENTE, 0.15)
extra = {  # comodos sem luz no export (qualidade 'leve' do motor poda luzes) ou muito grandes
    'quarto_casal': [([1.8, 2.5, 2.1], 26), ([0.5, 1.0, 1.1], 7)],
    'jardim': [([12.1, 2.5, 9.3], 40)],
    'quintal': [([5.5, 2.6, 14.5], 55), ([10.5, 2.6, 14.5], 55)],
    'dispensa': [([1.2, 2.5, 9.7], 18)],
    'varanda': [([3.5, 2.5, 5.2], 60), ([7.0, 2.5, 5.2], 60)],
    'piscina': [([4.5, -0.55, 10.0], 27), ([9.0, -0.55, 10.0], 27), ([6.9, -0.55, 11.5], 20)],
    'garagem': [([1.5, 2.5, 11.4], 16), ([1.5, 2.5, 15.0], 16)],
    'banheiro': [([1.2, 2.5, 6.9], 12)],
}
for rid, lst in extra.items():
    for pos, i in lst:
        sub = rid == 'piscina'
        add_point(rid, pos, i * FATOR * (1.6 if sub else 1), (0.1, 0.9, 0.95) if sub else QUENTE, 0.15)

# estudio: sol quente suave + area grande + ceu de preenchimento
sol = bpy.data.lights.new('sol', 'SUN'); sol.energy = 1.7; sol.angle = math.radians(7); sol.color = (1.0, 0.86, 0.68)
so = bpy.data.objects.new('sol', sol); sc.collection.objects.link(so); so.lightgroup = 'estudio'
so.rotation_euler = Vector((-0.6, 1.1, 0.55)).to_track_quat('-Z', 'Y').to_euler()
so.rotation_euler = (math.radians(52), 0, math.radians(-38))
area = bpy.data.lights.new('area', 'AREA'); area.energy = 1800; area.size = 14; area.color = (1.0, 0.93, 0.85)
ao = bpy.data.objects.new('area', area); sc.collection.objects.link(ao); ao.lightgroup = 'estudio'
ao.location = (6.5, -8, 20); ao.rotation_euler = (math.radians(10), 0, 0)
w = bpy.data.worlds.new('mundo'); w.use_nodes = True
bg = w.node_tree.nodes['Background']; bg.inputs['Color'].default_value = (0.55, 0.6, 0.72, 1); bg.inputs['Strength'].default_value = 0.16
w.lightgroup = 'estudio'; sc.world = w

# ---------------------------------------------------------------- camera
cam3 = CENA['cam']
camd = bpy.data.cameras.new('cam'); camd.sensor_fit = 'VERTICAL'; camd.angle = math.radians(cam3['fov'] * 0.92); camd.clip_start = 0.1; camd.clip_end = 300
camo = bpy.data.objects.new('cam', camd); sc.collection.objects.link(camo); sc.camera = camo
TARGET = b3(cam3['target']); POS0 = b3(cam3['position'])
def poe_camera(ang_graus=0.0):
    off = POS0 - TARGET
    rot = Matrix.Rotation(math.radians(ang_graus), 3, 'Z')
    camo.location = TARGET + rot @ off
    camo.rotation_euler = (TARGET - camo.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.view_layer.update()
poe_camera(0)

# ---------------------------------------------------------------- render
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = AMOSTRAS
sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.03
sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'
sc.cycles.max_bounces = 6; sc.cycles.diffuse_bounces = 3; sc.cycles.glossy_bounces = 3
sc.cycles.transmission_bounces = 6; sc.cycles.transparent_max_bounces = 6; sc.cycles.volume_bounces = 0
sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
sc.cycles.sample_clamp_indirect = 8
sc.render.threads_mode = 'AUTO'
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'None'
sc.render.film_transparent = True
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'; sc.render.image_settings.compression = 15

def res(w, h):
    sc.render.resolution_x = int(w * ESCALA); sc.render.resolution_y = int(h * ESCALA); sc.render.resolution_percentage = 100

def acender(comodos):
    """so os comodos listados ficam acesos (luzes + emissivos); estudio sempre."""
    for g, lst in luzes.items():
        for o in lst: o.hide_render = g not in comodos
    for o, p, s, rid in emissivos:
        p.inputs['Emission Strength'].default_value = s if rid in comodos else 0.0

def render_to(path):
    sc.render.filepath = path
    t = time.time(); bpy.ops.render.render(write_still=True); return time.time() - t

if os.environ.get('DBG_RAY'):
    dg = bpy.context.evaluated_depsgraph_get()
    for tgt in ([6.5, -9.8, 0.0], [8.6, -9.8, 0.0], [5.0, -10.5, -0.3]):
        d = (Vector(tgt) - camo.location).normalized()
        o = camo.location.copy()
        for k in range(4):
            ok, loc, nor, idx, ob, mt = sc.ray_cast(dg, o, d)
            if not ok: break
            print('RAY', tgt, k, ob.name, [s.material.name for s in ob.material_slots], [round(x, 2) for x in loc], ob.lightgroup)
            o = loc + d * 0.001
if os.environ.get('DBG_AGUA'):
    for o in bpy.data.objects:
        if o.type == 'MESH' and any(s.material and s.material.name == 'agua' for s in o.material_slots):
            if os.environ['DBG_AGUA'] == 'hide': o.hide_render = True
            print('AGUA obj', o.name, o.matrix_world.translation, o.dimensions, [round(v, 2) for v in (o.matrix_world @ Vector(o.bound_box[0]))], [round(v, 2) for v in (o.matrix_world @ Vector(o.bound_box[6]))], o.lightgroup, o.visible_camera, o.hide_render)
if MODO in ('main', 'teste'):
    res(2400, 1500)
    acender(set(GRUPOS))
    sc.use_nodes = True
    nt = sc.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    rl = nt.nodes.new('CompositorNodeRLayers')
    print('SAIDAS RL:', [s.name for s in rl.outputs])
    fo = nt.nodes.new('CompositorNodeOutputFile'); fo.base_path = SAIDA
    fo.format.file_format = 'PNG'; fo.format.color_mode = 'RGBA'; fo.format.compression = 15
    fo.file_slots.clear()
    def slot(nome, sock, alpha=None, rgb=False):
        fo.file_slots.new(nome)
        i = len(fo.inputs) - 1
        dn = nt.nodes.new('CompositorNodeDenoise'); dn.prefilter = 'ACCURATE'
        nt.links.new(sock, dn.inputs[0]); sock = dn.outputs[0]
        if alpha is None:
            nt.links.new(sock, fo.inputs[i])
        else:
            sa = nt.nodes.new('CompositorNodeSetAlpha'); sa.mode = 'REPLACE_ALPHA'
            nt.links.new(sock, sa.inputs[0]); nt.links.new(alpha, sa.inputs[1]); nt.links.new(sa.outputs[0], fo.inputs[i])
    slot('base_', rl.outputs['Combined_estudio'], alpha=rl.outputs['Alpha'])
    for r in ROOMS: slot(r['id'] + '_', rl.outputs['Combined_' + r['id']])
    slot('noite_', rl.outputs['Image'], alpha=rl.outputs['Alpha'])
    dt = render_to(os.path.join(SAIDA, 'frame_tmp.png'))
    for f in glob.glob(os.path.join(SAIDA, '*0001.png')):
        dst = os.path.join(SAIDA, os.path.basename(f).replace('_0001.png', '.png'))
        if os.path.exists(dst): os.remove(dst)
        os.rename(f, dst)
    tmp = os.path.join(SAIDA, 'frame_tmp.png')
    if os.path.exists(tmp): os.remove(tmp)
    # pontos: pixel do centro de cada comodo na base (2400x1500)
    pts = {}
    for r in ROOMS:
        v = world_to_camera_view(sc, camo, b3(r['center']))
        pts[r['id']] = {'x': round(v.x * 2400), 'y': round((1 - v.y) * 1500), 'xr': round(v.x, 4), 'yr': round(1 - v.y, 4), 'label': r['label']}
    json.dump({'largura': 2400, 'altura': 1500, 'pontos': pts}, open(os.path.join(SAIDA, 'pontos.json'), 'w'), indent=1, ensure_ascii=False)
    print('TEMPO main %.1fs (render %.1fs)' % (time.time() - T0, dt))
elif MODO == 'giro':
    res(1600, 1000)
    sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.color_mode = 'RGB'; sc.render.image_settings.quality = 88
    # fundo escuro para o JPG (sem alfa)
    sc.render.film_transparent = False
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.55, 0.6, 0.72, 1)
    # fundo azul-marinho so na camera (camera ray): mistura Light Path
    wn = w.node_tree.nodes; lp = wn.new('ShaderNodeLightPath')
    b2 = wn.new('ShaderNodeBackground'); b2.inputs['Color'].default_value = (0.012, 0.02, 0.06, 1); b2.inputs['Strength'].default_value = 1
    out = wn['World Output']
    mix = wn.new('ShaderNodeMixShader')
    w.node_tree.links.new(lp.outputs['Is Camera Ray'], mix.inputs['Fac'])
    w.node_tree.links.new(bg.outputs[0], mix.inputs[1]); w.node_tree.links.new(b2.outputs[0], mix.inputs[2])
    w.node_tree.links.new(mix.outputs[0], out.inputs['Surface'])
    tip = set(['quarto', 'sala', 'piscina'])
    acender(tip)
    sc.use_nodes = False
    n = 12
    for i in range(n):
        ang = -12 + 24 * i / (n - 1)
        poe_camera(ang)
        dt = render_to(os.path.join(SAIDA, 'giro_%02d.jpg' % (i + 1)))
        print('giro %d ang %.1f %.1fs' % (i + 1, ang, dt), flush=True)
    print('TEMPO giro %.1fs' % (time.time() - T0))
