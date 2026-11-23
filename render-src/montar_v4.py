"""v4 PREMIUM: materiais procedurais, bevel, luz de estudio, pos (glare+vinheta), adaptativo 0.01, OIDN com albedo+normal.
Monta a cena no Blender e renderiza (Cycles CPU + OpenImageDenoise + AgX).
Uso: blender -b -P render/montar.py -- MODO [amostras] [escala] [pasta_saida]
  MODO: main  -> base.png, <comodo>.png (so a luz do comodo), noite.png, pontos.json  (2880x1800 x ESCALA)
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

# ---------------------------------------------------------------- carro original (NAO mexer)
def _desc(o):
    for c in o.children:
        yield c; yield from _desc(c)
CAR = set(d for d in _desc(bpy.data.objects['Node_64']) if d.type == 'MESH')  # raiz do carro (era Node_65 antes do re-export; geometria conferida igual)
CAR_MATS = set(s_.material.name for o in CAR for s_ in o.material_slots if s_.material)
for o in bpy.data.objects:   # quem nao e carro e usa material do carro ganha copia propria
    if o.type == 'MESH' and o not in CAR:
        for s_ in o.material_slots:
            if s_.material and s_.material.name in CAR_MATS: s_.material = s_.material.copy()
print('CARRO', len(CAR), sorted(CAR_MATS))
# ---------------------------------------------------------------- materiais
def principled(m):
    return m.node_tree.nodes.get('Principled BSDF') if m.use_nodes and m.node_tree else None

def lum(c): return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]

emissivos = []   # (obj, material, strength_original, grupo)
mat_tipo = {}
for m in bpy.data.materials:
    if m.name in CAR_MATS: mat_tipo[m.name] = 'carro'; continue
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
        p.inputs['Base Color'].default_value = (0.55, 0.85, 0.72, 1)  # tom verde
    elif emi > 0.01:
        tipo = 'luz'
    elif metal > 0.5:
        tipo = 'metal'
        p.inputs['Roughness'].default_value = max(rough, 0.22)
    elif lum(col) < 0.03:
        tipo = 'preto'
        p.inputs['Roughness'].default_value = 0.38
        p.inputs['Specular IOR Level'].default_value = 0.45
    elif lum(col) > 0.6 and max(col[:3]) - min(col[:3]) < 0.12:
        tipo = 'parede'
        p.inputs['Roughness'].default_value = max(rough, 0.82)
    elif col[0] > col[2] * 1.5 and lum(col) < 0.45:
        tipo = 'madeira'
        p.inputs['Roughness'].default_value = min(max(rough, 0.45), 0.6)
    else:
        tipo = 'outro'
        p.inputs['Roughness'].default_value = max(rough, 0.4)
    # ---- v2: paleta mais rica e escura
    pc = p.inputs['Base Color'].default_value
    def setc(r, g, b): p.inputs['Base Color'].default_value = (r, g, b, 1)
    if m.name in ('Material_0',):          # laje-base: pedra/concreto escuro
        setc(0.10, 0.09, 0.085); p.inputs['Roughness'].default_value = 0.8; tipo = 'laje'
    elif m.name in ('Material_2', 'Material_10', 'Material_11', 'Material_12', 'Material_13', 'Material_73'):   # chao externo: pedra bege
        setc(0.36, 0.28, 0.19); p.inputs['Roughness'].default_value = 0.7; tipo = 'pedra'
    elif tipo == 'madeira':
        setc(pc[0] * 0.80, pc[1] * 0.72, pc[2] * 0.62)   # v4b: carvalho mel, menos laranja
    elif tipo == 'parede':
        k = 0.68; setc(pc[0] * k, pc[1] * k * 0.98, pc[2] * k * 0.94)
    elif tipo == 'outro':
        L = lum(pc)
        if L > 0.5: setc(pc[0] * 0.8, pc[1] * 0.74, pc[2] * 0.62)   # linho bege / claros
        elif max(pc[:3]) - min(pc[:3]) > 0.15: setc(pc[0] * 0.85, pc[1] * 0.85, pc[2] * 0.85)
    elif tipo == 'preto':
        setc(0.028, 0.027, 0.026)   # v4b: grafite, nao preto de jogo
    if m.name == 'Material_22':   # pintura branca brilhante do up!
        setc(0.8, 0.8, 0.78); p.inputs['Metallic'].default_value = 0.0; p.inputs['Roughness'].default_value = 0.12
        p.inputs['Coat Weight'].default_value = 0.6
    if m.name == 'Material_23':   # vidros do carro escuros
        p.inputs['Transmission Weight'].default_value = 0.0; setc(0.004, 0.006, 0.008); p.inputs['Roughness'].default_value = 0.05
        p.inputs['Metallic'].default_value = 0.3
    if m.name == 'Material_25':   # inox/metais: um pouco mais escuros
        p.inputs['Roughness'].default_value = 0.3
    if p.inputs['Base Color'].is_linked and m.name != 'Material_0':   # textura: multiplica por tinta
        lk = p.inputs['Base Color'].links[0]; src = lk.from_socket
        mx = m.node_tree.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
        mx.inputs[0].default_value = 1.0
        mx.inputs[7].default_value = (0.52, 0.45, 0.36, 1) if m.name in ('Material_2', 'Material_10', 'Material_11', 'Material_12', 'Material_13', 'Material_73') else (0.80, 0.66, 0.46, 1)   # v4b: piso de tabuas mais carvalho-mel, menos salmao
        m.node_tree.links.new(src, mx.inputs[6]); m.node_tree.links.new(mx.outputs[2], p.inputs['Base Color'])
    mat_tipo[m.name] = tipo

# v2: pisos externos baixos e claros -> pedra bege
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    ws = [o.matrix_world @ Vector(v) for v in o.bound_box]
    zs = [w.z for w in ws]; xs = [w.x for w in ws]; ys = [w.y for w in ws]
    if max(zs) < 0.12 and (max(zs) - min(zs)) < 0.2 and (max(xs) - min(xs)) * (max(ys) - min(ys)) > 6:
        for s_ in o.material_slots:
            m_ = s_.material
            if m_ and mat_tipo.get(m_.name) in ('parede', 'outro', 'pedra'):
                p_ = principled(m_)
                if lum(p_.inputs['Base Color'].default_value) > 0.2:
                    p_.inputs['Base Color'].default_value = (0.34, 0.265, 0.18, 1); p_.inputs['Roughness'].default_value = 0.7

# ---------------------------------------------------------------- v4: materiais procedurais (cores do modelo preservadas)
def _srcbase(p):
    sk = p.inputs['Base Color']
    return (sk.links[0].from_socket, None) if sk.is_linked else (None, tuple(sk.default_value))

def detalhar(m, tipo):
    nt = m.node_tree; p = principled(m)
    if not p: return
    N = nt.nodes.new; L = nt.links.new
    tc = N('ShaderNodeTexCoord')
    def mapping(sx=1.0, sy=1.0, sz=1.0):
        mp = N('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (sx, sy, sz); L(tc.outputs['Object'], mp.inputs['Vector']); return mp
    def noise(sc_, det=6, rough=0.55, mp=None, dist=0.0):
        n = N('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = sc_; n.inputs['Detail'].default_value = det; n.inputs['Roughness'].default_value = rough
        if dist: n.inputs['Distortion'].default_value = dist
        L((mp or mapping()).outputs[0], n.inputs['Vector']); return n
    def rng(sock, lo, hi, a=0.0, b=1.0):
        r = N('ShaderNodeMapRange'); r.inputs[1].default_value = a; r.inputs[2].default_value = b; r.inputs[3].default_value = lo; r.inputs[4].default_value = hi; r.clamp = True
        L(sock, r.inputs[0]); return r.outputs[0]
    def tint(fac_sock):   # multiplica a cor-base atual (textura ou cor) pela variacao
        src, dv = _srcbase(p)
        mx = N('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1.0
        if src is not None: L(src, mx.inputs[6])
        else: mx.inputs[6].default_value = dv
        L(fac_sock, mx.inputs[7]); L(mx.outputs[2], p.inputs['Base Color'])
    def bump(sock, forca, dist=0.01):
        bp = N('ShaderNodeBump'); bp.inputs['Strength'].default_value = forca; bp.inputs['Distance'].default_value = dist
        L(sock, bp.inputs['Height'])
        if p.inputs['Normal'].is_linked: L(p.inputs['Normal'].links[0].from_socket, bp.inputs['Normal'])
        L(bp.outputs['Normal'], p.inputs['Normal']); return bp
    def rugo(sock, lo, hi):
        L(rng(sock, lo, hi), p.inputs['Roughness'])
    linked = p.inputs['Base Color'].is_linked
    r0 = p.inputs['Roughness'].default_value
    if tipo == 'madeira':
        mp = mapping(0.22, 1.0, 1.0)
        wv = N('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'Y'; wv.wave_profile = 'SAW'
        wv.inputs['Scale'].default_value = 16; wv.inputs['Distortion'].default_value = 6; wv.inputs['Detail'].default_value = 3; wv.inputs['Detail Scale'].default_value = 1.6; wv.inputs['Detail Roughness'].default_value = 0.6
        L(mp.outputs[0], wv.inputs['Vector'])
        nz = noise(5, 4, 0.5, mapping(1, 0.6, 1))
        g = N('ShaderNodeMath'); g.operation = 'ADD'; L(wv.outputs['Fac'], g.inputs[0]); L(nz.outputs['Fac'], g.inputs[1])
        tint(rng(g.outputs[0], 0.82, 1.08, 0.2, 1.4)); bump(wv.outputs['Fac'], 0.12, 0.006); rugo(nz.outputs['Fac'], max(r0 - 0.08, 0.3), r0 + 0.12)
    elif tipo == 'parede' and linked:   # v4b: piso de tabuas (textura do modelo): juntas em relevo e acetinado
        src, _ = _srcbase(p)
        bw = N('ShaderNodeRGBToBW'); L(src, bw.inputs[0])
        n2 = noise(2.5, 3, 0.5)
        tint(rng(n2.outputs['Fac'], 0.92, 1.06, 0.3, 0.7)); bump(bw.outputs[0], 0.35, 0.003); rugo(n2.outputs['Fac'], 0.38, 0.55)
    elif tipo == 'parede':
        n1 = noise(220, 8, 0.6); n2 = noise(2.5, 3, 0.5)
        tint(rng(n2.outputs['Fac'], 0.94, 1.05, 0.3, 0.7)); bump(n1.outputs['Fac'], 0.09, 0.004); rugo(n2.outputs['Fac'], 0.72, 0.92)
    elif tipo == 'laje':
        n1 = noise(7, 10, 0.6); n2 = noise(140, 8, 0.6)
        tint(rng(n1.outputs['Fac'], 0.7, 1.25, 0.3, 0.7)); bump(n2.outputs['Fac'], 0.35, 0.008); rugo(n1.outputs['Fac'], 0.65, 0.92)
    elif tipo == 'pedra':
        if linked:   # ja tem juntas na textura do modelo: so variacao e relevo
            n1 = noise(2.2, 6, 0.55); n2 = noise(160, 7, 0.6)
            tint(rng(n1.outputs['Fac'], 0.82, 1.14, 0.3, 0.7)); bump(n2.outputs['Fac'], 0.18, 0.004); rugo(n1.outputs['Fac'], 0.45, 0.75)
        else:
            bk = N('ShaderNodeTexBrick'); bk.offset = 0.0; bk.inputs['Scale'].default_value = 1.0; bk.inputs['Mortar Size'].default_value = 0.012; bk.inputs['Mortar Smooth'].default_value = 0.1
            bk.inputs['Brick Width'].default_value = 0.6; bk.inputs['Row Height'].default_value = 0.6; bk.inputs['Bias'].default_value = 0.0
            bk.inputs['Color1'].default_value = (1, 1, 1, 1); bk.inputs['Color2'].default_value = (0.86, 0.86, 0.86, 1); bk.inputs['Mortar'].default_value = (0.42, 0.40, 0.38, 1)
            L(mapping().outputs[0], bk.inputs['Vector'])
            n1 = noise(3, 6, 0.55)
            mm = N('ShaderNodeMix'); mm.data_type = 'RGBA'; mm.blend_type = 'MULTIPLY'; mm.inputs[0].default_value = 1.0; L(bk.outputs['Color'], mm.inputs[6]); L(rng(n1.outputs['Fac'], 0.85, 1.12, 0.3, 0.7), mm.inputs[7])
            tint(mm.outputs[2]); bump(bk.outputs['Fac'], 0.5, 0.01)
            rugo(n1.outputs['Fac'], 0.45, 0.75)
    elif tipo == 'metal':
        n1 = noise(2, 2, 0.5, mapping(400, 3, 3)); n2 = noise(40, 4, 0.5)
        bump(n1.outputs['Fac'], 0.12, 0.002); rugo(n2.outputs['Fac'], max(r0 - 0.06, 0.22), r0 + 0.14); tint(rng(n2.outputs['Fac'], 0.88, 1.08, 0.3, 0.7))
    elif tipo == 'preto':
        n1 = noise(300, 4, 0.5); bump(n1.outputs['Fac'], 0.06, 0.002)
    elif tipo == 'outro':
        c = p.inputs['Base Color'].default_value
        verde = (not linked) and c[1] > c[0] * 1.15 and c[1] > c[2] * 1.15
        if verde:   # grama / folhagem
            n1 = noise(30, 6, 0.6); n2 = noise(120, 4, 0.5); n3 = noise(320, 10, 0.7)
            a = N('ShaderNodeMath'); a.operation = 'ADD'; L(n1.outputs['Fac'], a.inputs[0]); L(n2.outputs['Fac'], a.inputs[1])
            tint(rng(a.outputs[0], 0.6, 1.3, 0.35, 1.25)); bump(n3.outputs['Fac'], 0.8, 0.012); p.inputs['Roughness'].default_value = 0.85
        else:       # tecido / linho: trama fina
            w1 = N('ShaderNodeTexWave'); w1.wave_type = 'BANDS'; w1.bands_direction = 'X'; w1.inputs['Scale'].default_value = 600; w1.inputs['Distortion'].default_value = 0.6
            w2 = N('ShaderNodeTexWave'); w2.wave_type = 'BANDS'; w2.bands_direction = 'Y'; w2.inputs['Scale'].default_value = 600; w2.inputs['Distortion'].default_value = 0.6
            mp = mapping(); L(mp.outputs[0], w1.inputs['Vector']); L(mp.outputs[0], w2.inputs['Vector'])
            s_ = N('ShaderNodeMath'); s_.operation = 'MULTIPLY'; L(w1.outputs['Fac'], s_.inputs[0]); L(w2.outputs['Fac'], s_.inputs[1])
            n1 = noise(35, 5, 0.55); n2 = noise(260, 3, 0.5)
            tint(rng(n1.outputs['Fac'], 0.88, 1.1, 0.3, 0.7)); bump(s_.outputs[0], 0.35, 0.002)
            p.inputs['Sheen Weight'].default_value = 0.35; p.inputs['Sheen Roughness'].default_value = 0.5
            rugo(n2.outputs['Fac'], 0.7, 0.95)
    elif tipo == 'agua':
        n1 = noise(7, 5, 0.5, mapping(1, 1, 1), 0.6); n2 = noise(26, 4, 0.5)
        a = N('ShaderNodeMath'); a.operation = 'ADD'; L(n1.outputs['Fac'], a.inputs[0]); L(n2.outputs['Fac'], a.inputs[1])
        bump(a.outputs[0], 0.12, 0.05)
        lw = N('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.35
        cr = N('ShaderNodeValToRGB'); cr.color_ramp.elements[0].position = 0.0; cr.color_ramp.elements[0].color = (0.02, 0.48, 0.58, 1); cr.color_ramp.elements[1].position = 1.0; cr.color_ramp.elements[1].color = (0.0, 0.26, 0.40, 1)
        L(lw.outputs['Facing'], cr.inputs['Fac']); L(cr.outputs['Color'], p.inputs['Base Color'])
        vo = N('ShaderNodeTexVoronoi'); vo.feature = 'DISTANCE_TO_EDGE'; vo.inputs['Scale'].default_value = 5.5; L(mapping().outputs[0], vo.inputs['Vector'])
        cm = N('ShaderNodeMapRange'); cm.inputs[1].default_value = 0.0; cm.inputs[2].default_value = 0.35; cm.inputs[3].default_value = 1.0; cm.inputs[4].default_value = 0.62; cm.clamp = True; L(vo.outputs['Distance'], cm.inputs[0])
        em = N('ShaderNodeMix'); em.data_type = 'RGBA'; em.blend_type = 'MULTIPLY'; em.inputs[0].default_value = 1.0; em.inputs[6].default_value = (0.05, 0.85, 0.9, 1); L(cm.outputs[0], em.inputs[7]); L(em.outputs[2], p.inputs['Emission Color'])
        p.inputs['Roughness'].default_value = 0.05; p.inputs['Specular IOR Level'].default_value = 0.5
    elif tipo == 'vidro':   # vidro fino correto: Fresnel IOR 1.45 entre transmissao esverdeada e reflexo
        for l in list(nt.links):
            if l.to_node.type == 'OUTPUT_MATERIAL': nt.links.remove(l)
        tr = N('ShaderNodeBsdfTransparent'); tr.inputs['Color'].default_value = (0.62, 0.88, 0.78, 1)
        gl = N('ShaderNodeBsdfGlossy'); gl.inputs['Roughness'].default_value = 0.02; gl.inputs['Color'].default_value = (0.9, 1.0, 0.95, 1)
        fr = N('ShaderNodeFresnel'); fr.inputs['IOR'].default_value = 1.45
        mx = N('ShaderNodeMixShader'); L(fr.outputs[0], mx.inputs[0]); L(tr.outputs[0], mx.inputs[1]); L(gl.outputs[0], mx.inputs[2])
        out_ = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'); L(mx.outputs[0], out_.inputs['Surface'])

for _m in list(bpy.data.materials):
    _t = mat_tipo.get(_m.name)
    if _t and _t not in ('carro', 'invisivel', 'luz'):
        try: detalhar(_m, _t)
        except Exception as e: print('DETALHE falhou', _m.name, _t, e)

# ---------------------------------------------------------------- objetos: lightgroups, bevel
# v4b: halos/tampas 'unlit' do three somem do render (transparentes, mas entravam no albedo do OIDN e o denoise desenhava uma elipse clara no piso)
_inv = 0
for o in bpy.data.objects:
    if o.type == 'MESH' and o.material_slots and all(s_.material and mat_tipo.get(s_.material.name) == 'invisivel' for s_ in o.material_slots):
        o.hide_render = True; _inv += 1
print('INVISIVEIS ocultos', _inv, [o.name for o in bpy.data.objects if o.hide_render])
mesh_objs = [o for o in bpy.data.objects if o.type == 'MESH']
bevelados = []
for o in mesh_objs:
    if o in CAR: continue
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
            principled(m).inputs['Emission Strength'].default_value = 0.3
    if any(t in ('agua', 'vidro') for t in tipos): o.visible_shadow = False   # vidro nao bloqueia a luz (Cycles nao refrata luz direta)
    # bevel (so em solidos): remove doubles + bevel fino
    if any(t in ('agua', 'vidro') for t in tipos) or not o.data.polygons: continue
    dims = o.dimensions
    mn = min(d for d in dims if d > 1e-4) if any(d > 1e-4 for d in dims) else 0
    if mn < 0.025 or min(dims) < 0.012: continue   # v4b: planos/pisos sem espessura ficam planos (suavizar gerava elipse clara no deck)
    me = o.data
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bm.to_mesh(me); bm.free()
    for poly in me.polygons: poly.use_smooth = True
    bpy.context.view_layer.objects.active = o
    try: bpy.ops.mesh.customdata_custom_splitnormals_clear()
    except Exception: pass
    md = o.modifiers.new('bevel', 'BEVEL')
    md.width = min(0.010, mn * 0.16); md.segments = 2; md.limit_method = 'ANGLE'; md.angle_limit = math.radians(30); md.harden_normals = True
    bevelados.append(o)

# suavizado por angulo (35 graus) nos solidos com bevel
try:
    bpy.ops.object.select_all(action='DESELECT')
    for o in bevelados: o.select_set(True)
    bpy.context.view_layer.objects.active = bevelados[0]
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
except Exception as e: print('shade_smooth_by_angle falhou', e)
print('BEVEL em', len(bevelados), 'objetos')

# ---------------------------------------------------------------- luzes
GRUPOS = ['estudio'] + [r['id'] for r in ROOMS]
vl = bpy.context.view_layer
for g in GRUPOS:
    vl.lightgroups.add(name=g)
K = 2700
QUENTE = (1.0, 0.62, 0.32)   # v4b: ~3000 K (linear), menos laranja
luzes = {}  # grupo -> [obj]
def add_point(room, pos3, power, color, radius=0.12, nome=None):
    d = bpy.data.lights.new(nome or ('luz_' + room), 'POINT')
    d.energy = power; d.color = color; d.shadow_soft_size = radius
    o = bpy.data.objects.new(d.name, d); sc.collection.objects.link(o)
    o.location = b3(pos3); o.lightgroup = room
    luzes.setdefault(room, []).append(o)
    return o
FATOR = 15.0 * float(os.environ.get('ROOM_K', '0.55'))   # candela do motor -> watts do Blender (calibrado no teste)
tem = {}
for L in CENA['lights']:
    tem.setdefault(L['room'], []).append(L)
    sub = L['room'] == 'piscina'
    add_point(L['room'], L['pos'], L['i'] * FATOR * (1.6 if sub else 1), (0.1, 0.9, 0.95) if sub else QUENTE, 0.30)
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
        add_point(rid, pos, i * FATOR * (1.6 if sub else 1), (0.1, 0.9, 0.95) if sub else QUENTE, 0.30)

# v4b: cupulas/pendentes que envolvem a lampada nao fazem sombra (senao desenham uma elipse dura no piso)
_bbs = []
for o in bpy.data.objects:
    if o.type != 'MESH' or o in CAR: continue
    ws = [o.matrix_world @ Vector(v) for v in o.bound_box]
    mn = Vector([min(w[i] for w in ws) for i in range(3)]); mx = Vector([max(w[i] for w in ws) for i in range(3)])
    if max(mx - mn) < 1.2: _bbs.append((o, mn, mx))
_n = 0
for g_, lst in luzes.items():
    if g_ == 'piscina': continue
    for lo in lst:
        q = lo.location
        for o, mn, mx in _bbs:
            if all(mn[i] - 0.08 <= q[i] <= mx[i] + 0.08 for i in range(3)) and o.visible_shadow:
                o.visible_shadow = False; _n += 1
print('CUPULAS sem sombra', _n)

# luz subaquatica so na agua/bacia da piscina (light linking)
rec = bpy.data.collections.new('so_agua'); 
for o in bpy.data.objects:
    if o.type != 'MESH' or o in CAR: continue
    c = sum((o.matrix_world @ Vector(v) for v in o.bound_box), Vector()) / 8
    ag = any(s_.material and s_.material.name == 'agua' for s_ in o.material_slots)
    bacia = c.z < 0.0 and 2.0 < c.x < 10.2 and -11.6 < c.y < -8.0
    if ag or bacia: rec.objects.link(o)
print('RECEPTORES agua', len(rec.objects))
for o in luzes.get('piscina', []):
    try: o.light_linking.receiver_collection = rec
    except Exception as e: print('LL falhou', e); o.data.energy *= 0.25
# estudio v4: area grande principal (macia, quente) + recorte + ambiente baixo. Base exposta POR LUZ (sem gama em pos).
EST_K = float(os.environ.get('EST_K', '1.5'))
sol = bpy.data.lights.new('sol', 'SUN'); sol.energy = 1.4 * EST_K; sol.angle = math.radians(9); sol.color = (1.0, 0.80, 0.62)
so = bpy.data.objects.new('sol', sol); sc.collection.objects.link(so); so.lightgroup = 'estudio'
so.rotation_euler = (math.radians(52), 0, math.radians(-38))
area = bpy.data.lights.new('area', 'AREA'); area.energy = 2600 * EST_K; area.size = 22; area.color = (1.0, 0.90, 0.80)
ao = bpy.data.objects.new('area', area); sc.collection.objects.link(ao); ao.lightgroup = 'estudio'
ao.location = (6.5, -8, 20); ao.rotation_euler = (math.radians(10), 0, 0)
rim = bpy.data.lights.new('recorte', 'AREA'); rim.energy = float(os.environ.get('RIM','1500')) * EST_K; rim.size = 10; rim.color = (0.78, 0.86, 1.0)   # v4b: recorte frio (lua) separa a maquete do fundo
ro = bpy.data.objects.new('recorte', rim); sc.collection.objects.link(ro); ro.lightgroup = 'estudio'
ro.location = (-9, 20, 11); ro.rotation_euler = (Vector((6.5, -6, 0)) - ro.location).to_track_quat('-Z', 'Y').to_euler()
w = bpy.data.worlds.new('mundo'); w.use_nodes = True
bg = w.node_tree.nodes['Background']; bg.inputs['Color'].default_value = (0.55, 0.6, 0.72, 1); bg.inputs['Strength'].default_value = 0.07 * EST_K
w.lightgroup = 'estudio'; sc.world = w

# sombra suave sob a laje: plano so visivel pela camera, preto com alfa em degrade (nao interfere na luz)
sp = bpy.data.objects.new('sombra', bpy.data.meshes.new('sombra'))
bm_ = bmesh.new(); bmesh.ops.create_grid(bm_, x_segments=1, y_segments=1, size=0.5); bm_.to_mesh(sp.data); bm_.free()
sc.collection.objects.link(sp); sp.location = (7.0, -8.5, -1.32); sp.scale = (24, 26, 1)
sp.visible_shadow = False; sp.visible_glossy = False; sp.visible_diffuse = False; sp.visible_transmission = False; sp.visible_volume_scatter = False
uvl = sp.data.uv_layers.new(name='UVMap')
sm = bpy.data.materials.new('sombra_m'); sm.use_nodes = True; nt_ = sm.node_tree; nt_.nodes.clear()
N = nt_.nodes.new; L_ = nt_.links.new
tc = N('ShaderNodeTexCoord'); sx = N('ShaderNodeSeparateXYZ'); L_(tc.outputs['Generated'], sx.inputs[0])
def ab(sock):
    a = N('ShaderNodeMath'); a.operation = 'SUBTRACT'; a.inputs[1].default_value = 0.5; L_(sock, a.inputs[0])
    b = N('ShaderNodeMath'); b.operation = 'ABSOLUTE'; L_(a.outputs[0], b.inputs[0])
    c = N('ShaderNodeMath'); c.operation = 'MULTIPLY'; c.inputs[1].default_value = 2.0; L_(b.outputs[0], c.inputs[0]); return c.outputs[0]
mxx = N('ShaderNodeMath'); mxx.operation = 'MAXIMUM'; L_(ab(sx.outputs[0]), mxx.inputs[0]); L_(ab(sx.outputs[1]), mxx.inputs[1])
mr = N('ShaderNodeMapRange'); mr.inputs[1].default_value = 0.55; mr.inputs[2].default_value = 1.0; mr.inputs[3].default_value = 0.6; mr.inputs[4].default_value = 0.0; mr.interpolation_type = 'SMOOTHSTEP'; mr.clamp = True
L_(mxx.outputs[0], mr.inputs[0])
tr = N('ShaderNodeBsdfTransparent'); em = N('ShaderNodeEmission'); em.inputs[0].default_value = (0, 0, 0, 1); em.inputs[1].default_value = 1
mix = N('ShaderNodeMixShader'); L_(mr.outputs[0], mix.inputs[0]); L_(tr.outputs[0], mix.inputs[1]); L_(em.outputs[0], mix.inputs[2])
out = N('ShaderNodeOutputMaterial'); L_(mix.outputs[0], out.inputs[0])
sp.data.materials.append(sm)

# ---------------------------------------------------------------- render
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = AMOSTRAS
sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.01; sc.cycles.adaptive_min_samples = 8
sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'
try: sc.cycles.denoising_input_passes = 'RGB_ALBEDO_NORMAL'; sc.cycles.denoising_prefilter = 'ACCURATE'
except Exception as e: print('denoise passes', e)
sc.cycles.max_bounces = 6; sc.cycles.diffuse_bounces = 3; sc.cycles.glossy_bounces = 3
sc.cycles.transmission_bounces = 6; sc.cycles.transparent_max_bounces = 8; sc.cycles.volume_bounces = 0
sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
sc.cycles.sample_clamp_indirect = 6; sc.cycles.sample_clamp_direct = 0
sc.render.threads_mode = 'AUTO'
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - Medium High Contrast'
except Exception: sc.view_settings.look = 'AgX - High Contrast'
sc.view_settings.exposure = float(os.environ.get('EXPO', '0.0'))
sc.render.film_transparent = True
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'; sc.render.image_settings.compression = 15
vl.cycles.denoising_store_passes = True

POS_MR = []; POS_HS = []
SAT_V = float(os.environ.get('SAT', '1.04'))
def pos_cadeia(nt, sock, vig=0.22, glare=True):
    """Glare (fog glow, so nas luzes) + vinheta suave. Retorna o socket final."""
    if glare and os.environ.get('GLARE','1') == '1':
        try:
            gl = nt.nodes.new('CompositorNodeGlare'); gl.glare_type = 'FOG_GLOW'; gl.quality = 'MEDIUM'; gl.threshold = float(os.environ.get('GTH','4.0')); gl.size = 6; gl.mix = -0.7
            nt.links.new(sock, gl.inputs[0]); sock = gl.outputs[0]
        except Exception as e: print('glare falhou', e)
    try:
        hs = nt.nodes.new('CompositorNodeHueSat'); hs.inputs['Saturation'].default_value = SAT_V; POS_HS.append(hs); hs.inputs['Value'].default_value = 1.0
        nt.links.new(sock, hs.inputs['Image']); sock = hs.outputs[0]
    except Exception as e: print('hue falhou', e)
    # v4b: vinheta por imagem gerada (mesma formula do costurar_v4). A Ellipse Mask + Blur do 4.5 saia com borda dura
    # (uma elipse clara no meio da maquete, parecia um tapete).
    import numpy as _np
    W_, H_ = sc.render.resolution_x * sc.render.resolution_percentage // 100, sc.render.resolution_y * sc.render.resolution_percentage // 100
    yy, xx = _np.mgrid[0:H_, 0:W_].astype(_np.float32)
    r_ = _np.sqrt(((xx / W_ - 0.5) / 0.62) ** 2 + ((yy / H_ - 0.5) / 0.60) ** 2)
    t_ = _np.clip((r_ - 0.45) / 0.65, 0, 1); t_ = t_ * t_ * (3 - 2 * t_)
    m_ = 1.0 - t_   # 1 no centro, 0 nos cantos
    im = bpy.data.images.new('vinheta_%dx%d' % (W_, H_), W_, H_, alpha=False, float_buffer=True)
    try: im.colorspace_settings.name = 'Non-Color'
    except Exception: pass
    px = _np.ones((H_, W_, 4), _np.float32); px[..., 0] = m_; px[..., 1] = m_; px[..., 2] = m_
    im.pixels.foreach_set(px.ravel())
    imn = nt.nodes.new('CompositorNodeImage'); imn.image = im
    mr = nt.nodes.new('CompositorNodeMapRange'); mr.inputs[3].default_value = 1.0 - vig; mr.inputs[4].default_value = 1.0
    nt.links.new(imn.outputs[0], mr.inputs[0])
    mx = nt.nodes.new('CompositorNodeMixRGB'); mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1.0
    nt.links.new(sock, mx.inputs[1]); nt.links.new(mr.outputs[0], mx.inputs[2])
    POS_MR.append(mr)
    return mx.outputs[0]

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
    res(2880, 1800)
    # STRIP='k/n': renderiza so uma faixa horizontal (com sobreposicao) -> pouca RAM; costurar com costurar_v4.py (que aplica glare/saturacao/vinheta)
    STRIP = os.environ.get('STRIP')
    if STRIP:
        _k, _n = [int(v) for v in STRIP.split('/')]
        H = sc.render.resolution_y; OV = 48
        y0 = max(0, _k * H // _n - (OV if _k > 0 else 0)); y1 = min(H, (_k + 1) * H // _n + (OV if _k < _n - 1 else 0))
        sc.render.use_border = True; sc.render.use_crop_to_border = True
        sc.render.border_min_x = 0.0; sc.render.border_max_x = 1.0
        sc.render.border_min_y = (H - y1 + 0.01) / H; sc.render.border_max_y = (H - y0 + 0.01) / H
        json.dump({'y0': y0, 'y1': y1, 'H': H}, open(os.path.join(SAIDA, 'faixa.json'), 'w'))
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
        nt.links.new(sock, dn.inputs[0]); nt.links.new(rl.outputs['Denoising Albedo'], dn.inputs[1]); nt.links.new(rl.outputs['Denoising Normal'], dn.inputs[2])
        sock = dn.outputs[0] if os.environ.get('STRIP') else pos_cadeia(nt, dn.outputs[0], glare=(nome != 'base_'))
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
        pts[r['id']] = {'x': round(v.x * sc.render.resolution_x), 'y': round((1 - v.y) * sc.render.resolution_y), 'xr': round(v.x, 4), 'yr': round(1 - v.y, 4), 'label': r['label']}
    json.dump({'largura': sc.render.resolution_x, 'altura': sc.render.resolution_y, 'pontos': pts}, open(os.path.join(SAIDA, 'pontos.json'), 'w'), indent=1, ensure_ascii=False)
    print('TEMPO main %.1fs (render %.1fs)' % (time.time() - T0, dt))
elif MODO == 'giro':
    res(1920, 1200)
    sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.color_mode = 'RGB'; sc.render.image_settings.quality = 92
    # fundo escuro para o JPG (sem alfa)
    sc.render.film_transparent = False
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.55, 0.6, 0.72, 1)
    # fundo azul-marinho so na camera (camera ray): mistura Light Path
    wn = w.node_tree.nodes; lp = wn.new('ShaderNodeLightPath')
    b2 = wn.new('ShaderNodeBackground'); b2.inputs['Color'].default_value = (0.012, 0.016, 0.04, 1); b2.inputs['Strength'].default_value = 1
    out = wn['World Output']
    mix = wn.new('ShaderNodeMixShader')
    w.node_tree.links.new(lp.outputs['Is Camera Ray'], mix.inputs['Fac'])
    w.node_tree.links.new(bg.outputs[0], mix.inputs[1]); w.node_tree.links.new(b2.outputs[0], mix.inputs[2])
    w.node_tree.links.new(mix.outputs[0], out.inputs['Surface'])
    tip = set(['quarto', 'sala', 'piscina'])
    acender(tip)
    sc.use_nodes = True; nt = sc.node_tree
    for n_ in list(nt.nodes): nt.nodes.remove(n_)
    rl = nt.nodes.new('CompositorNodeRLayers'); co = nt.nodes.new('CompositorNodeComposite')
    nt.links.new(pos_cadeia(nt, rl.outputs['Image']), co.inputs[0])
    n = int(os.environ.get('GIRO_N', '8'))
    GK = float(os.environ.get('GIRO_K', '0.4'))   # estudio mais baixo: giro e a versao 'noite com luzes tipicas'
    sol.energy *= GK; area.energy *= GK; rim.energy *= GK; bg.inputs['Strength'].default_value *= GK
    _gi = os.environ.get('GIRO_I')   # nuvem: um quadro por job (indice 0..n-1)
    for i in ([int(_gi)] if _gi is not None else range(n)):
        ang = (-8 + 16 * i / (n - 1)) if n > 1 else 0.0
        poe_camera(ang)
        dt = render_to(os.path.join(SAIDA, 'giro_%02d.jpg' % (i + 1)))
        print('giro %d ang %.1f %.1fs' % (i + 1, ang, dt), flush=True)
    print('TEMPO giro %.1fs' % (time.time() - T0))




