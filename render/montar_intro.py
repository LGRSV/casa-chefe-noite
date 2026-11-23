"""Intro cinematografica: casa vista da rua ao entardecer -> voo ate a camera exata da maquete.
Uso: blender -b -P render/montar_intro.py -- QUADROS LARGURAxALTURA AMOSTRAS PASTA_SAIDA [primeiro] [ultimo]
  ex.: -- 72 1280x800 16 C:/.../intro/quadros
Saida: intro_001..NNN.jpg (JPEG q82). Reaproveita o setup de montar_v3.py (mesmo glb, materiais, luzes)
executando-o ate a secao 'camera'. Coordenadas: three (x,y,z) -> blender (x,-z,y); a rua fica em y<-16 (blender).
O ultimo quadro usa a camera de cena.json (igual a render/web/base.webp) e o fundo vira #0e1630."""
import sys, os, math, json, time

AQUI = os.path.dirname(os.path.abspath(__file__))
_a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
NQ = int(_a[0]) if len(_a) > 0 else 72
RES = _a[1] if len(_a) > 1 else '1280x800'
AMOSTRAS = int(_a[2]) if len(_a) > 2 else 16
SAIDA = os.path.abspath(_a[3]) if len(_a) > 3 else os.path.join(AQUI, '..', 'intro', 'quadros')
I0 = int(_a[4]) if len(_a) > 4 else 1
I1 = int(_a[5]) if len(_a) > 5 else NQ
RW, RH = [int(v) for v in RES.lower().split('x')]
os.makedirs(SAIDA, exist_ok=True)

# ---- reaproveita o v3 ate antes da camera (glb, materiais, luzes, mundo, sombra)
src = open(os.path.join(AQUI, 'montar_v3.py'), encoding='utf-8').read()
corte = src.index('# ---------------------------------------------------------------- camera')
_argv = sys.argv
sys.argv = [_argv[0], '--', 'intro', str(AMOSTRAS), '0.5', SAIDA]
__file__ = os.path.join(AQUI, 'montar_v3.py')
exec(compile(src[:corte], 'montar_v3(setup)', 'exec'), globals())
sys.argv = _argv
T1 = time.time()

import bpy
from mathutils import Vector, Matrix

def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)

def bez(p0, p1, p2, p3, s):
    u = 1 - s
    return p0 * u ** 3 + p1 * 3 * u * u * s + p2 * 3 * u * s * s + p3 * s ** 3

# ---------------------------------------------------------------- cor de fundo exata (#0e1630 apos AgX)
def srgb8_lin(v):
    c = v / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def calibrar(alvo8):
    """acha a cor linear do mundo que, passando pelo mesmo AgX/exposicao, sai como o RGB 8-bit alvo."""
    s2 = bpy.data.scenes.new('calib')
    s2.render.engine = 'CYCLES'; s2.cycles.samples = 1; s2.cycles.use_denoising = False
    s2.render.resolution_x = 16; s2.render.resolution_y = 16; s2.render.resolution_percentage = 100
    s2.view_settings.view_transform = sc.view_settings.view_transform
    s2.view_settings.look = sc.view_settings.look
    s2.view_settings.exposure = sc.view_settings.exposure
    s2.render.image_settings.file_format = 'PNG'; s2.render.image_settings.color_mode = 'RGB'
    s2.render.image_settings.color_depth = '8'
    w2 = bpy.data.worlds.new('calib_w'); w2.use_nodes = True; s2.world = w2
    cd = bpy.data.cameras.new('c2'); co = bpy.data.objects.new('c2', cd); s2.collection.objects.link(co); s2.camera = co
    c = [srgb8_lin(v) for v in alvo8]
    p = os.path.join(SAIDA, '_calib.png')
    for it in range(24):
        b = w2.node_tree.nodes['Background']
        b.inputs['Color'].default_value = (c[0], c[1], c[2], 1); b.inputs['Strength'].default_value = 1
        s2.render.filepath = p
        bpy.ops.render.render(write_still=True, scene='calib')
        im = bpy.data.images.load(p, check_existing=False); im.colorspace_settings.name = 'Non-Color'
        px = list(im.pixels[0:3]); bpy.data.images.remove(im)
        m8 = [round(v * 255) for v in px]   # pixels do png ja em sRGB 0..1
        if all(abs(m8[k] - alvo8[k]) <= 0 for k in range(3)): break
        for k in range(3):
            if m8[k] != alvo8[k]:
                c[k] = max(c[k] * min(max(alvo8[k] / max(m8[k], 0.6), 0.5), 2.0) ** 0.9, 1e-6)
    print('CALIB', alvo8, '->', [round(v, 5) for v in c], 'saiu', m8, 'iter', it, flush=True)
    os.remove(p)
    bpy.data.scenes.remove(s2)
    return tuple(c)

sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - High Contrast'; sc.view_settings.exposure = -0.5
FUNDO = calibrar((0x0e, 0x16, 0x30))

# ---------------------------------------------------------------- mundo: ceu de entardecer animado
wt = w.node_tree
for n in list(wt.nodes): wt.nodes.remove(n)
N = wt.nodes.new; Lk = wt.links.new
out = N('ShaderNodeOutputWorld')
lp = N('ShaderNodeLightPath')
tcx = N('ShaderNodeTexCoord'); sepz = N('ShaderNodeSeparateXYZ'); Lk(tcx.outputs['Generated'], sepz.inputs[0])
ramp = N('ShaderNodeValToRGB')
ramp.color_ramp.interpolation = 'EASE'
# linear (pos, rgb): horizonte laranja -> rosa/violeta -> azul-profundo
stops = [(0.0, (1.0, 0.33, 0.07)), (0.045, (0.80, 0.22, 0.07)), (0.14, (0.30, 0.08, 0.14)), (0.32, (0.045, 0.04, 0.17)), (0.7, (0.008, 0.012, 0.07)), (1.0, (0.004, 0.008, 0.05))]
el = ramp.color_ramp.elements
while len(el) > 1: el.remove(el[-1])
el[0].position = stops[0][0]; el[0].color = stops[0][1] + (1,)
for pos, col in stops[1:]:
    e = el.new(pos); e.color = col + (1,)
Lk(sepz.outputs['Z'], ramp.inputs['Fac'])
kval = N('ShaderNodeValue'); kval.name = 'k_ceu'
mixk = N('ShaderNodeMix'); mixk.data_type = 'RGBA'; mixk.blend_type = 'MIX'
Lk(kval.outputs[0], mixk.inputs[0]); Lk(ramp.outputs['Color'], mixk.inputs[6])
mixk.inputs[7].default_value = FUNDO + (1,)
bcam = N('ShaderNodeBackground'); Lk(mixk.outputs[2], bcam.inputs['Color']); bcam.inputs['Strength'].default_value = 1.0
bdif = N('ShaderNodeBackground'); bdif.inputs['Color'].default_value = (0.55, 0.6, 0.72, 1); bdif.inputs['Strength'].default_value = 0.035
mxs = N('ShaderNodeMixShader'); Lk(lp.outputs['Is Camera Ray'], mxs.inputs['Fac']); Lk(bdif.outputs[0], mxs.inputs[1]); Lk(bcam.outputs[0], mxs.inputs[2])
Lk(mxs.outputs[0], out.inputs['Surface'])

# ---------------------------------------------------------------- rua e calcada (somem no fim)
gf = None   # no 'Value' compartilhado de fade do chao: 1 = visivel, 0 = transparente
fade_nodes = []
def mat_chao(nome, cor, rough, bump=0.0, escala=40.0):
    m = bpy.data.materials.new(nome); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    n_ = nt.nodes.new; l_ = nt.links.new
    pb = n_('ShaderNodeBsdfPrincipled'); pb.inputs['Base Color'].default_value = cor + (1,); pb.inputs['Roughness'].default_value = rough
    pb.inputs['Specular IOR Level'].default_value = 0.5
    if bump:
        tc = n_('ShaderNodeTexCoord'); ns = n_('ShaderNodeTexNoise'); ns.inputs['Scale'].default_value = escala; ns.inputs['Detail'].default_value = 6
        bp = n_('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump; bp.inputs['Distance'].default_value = 0.02
        l_(tc.outputs['Object'], ns.inputs['Vector']); l_(ns.outputs['Fac'], bp.inputs['Height']); l_(bp.outputs['Normal'], pb.inputs['Normal'])
        # variacao de tom no asfalto/pedra
        mr = n_('ShaderNodeMapRange'); mr.inputs[3].default_value = 0.75; mr.inputs[4].default_value = 1.2
        l_(ns.outputs['Fac'], mr.inputs[0])
        mx = n_('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1.0
        mx.inputs[6].default_value = cor + (1,); l_(mr.outputs[0], mx.inputs[7]); l_(mx.outputs[2], pb.inputs['Base Color'])
    tr = n_('ShaderNodeBsdfTransparent'); mix = n_('ShaderNodeMixShader'); v = n_('ShaderNodeValue')
    l_(v.outputs[0], mix.inputs[0]); l_(pb.outputs[0], mix.inputs[2]); l_(tr.outputs[0], mix.inputs[1])  # fac=gf: 0 -> transparente
    o_ = n_('ShaderNodeOutputMaterial'); l_(mix.outputs[0], o_.inputs[0])
    fade_nodes.append(v)
    return m

def caixa(nome, x0, x1, y0, y1, z0, z1, m):
    me = bpy.data.meshes.new(nome)
    vs = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    fs = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me.from_pydata(vs, [], fs); me.update()
    me.materials.append(m)
    o = bpy.data.objects.new(nome, me); sc.collection.objects.link(o)
    o.visible_shadow = True
    return o

m_terra = mat_chao('rua_terra', (0.030, 0.027, 0.024), 0.92, 0.3, 12)
m_asfalto = mat_chao('rua_asfalto', (0.028, 0.029, 0.034), 0.38, 0.5, 60)
m_calcada = mat_chao('rua_calcada', (0.17, 0.155, 0.14), 0.72, 0.25, 30)
m_meiofio = mat_chao('rua_meiofio', (0.22, 0.21, 0.2), 0.7)
X0, X1 = -300, 300
# terra em volta do lote (recorte: laje x -0.55..13.95, y -16.55..0.55; sem tampar a piscina)
caixa('terra_e', X0, -0.6, -300, 60, -0.30, -0.03, m_terra)
caixa('terra_d', 14.0, X1, -300, 60, -0.30, -0.03, m_terra)
caixa('terra_f', -0.6, 14.0, -300, -33.8, -0.30, -0.03, m_terra)
caixa('terra_t', -0.6, 14.0, 0.6, 60, -0.30, -0.03, m_terra)
caixa('rua_asfalto', X0, X1, -31.0, -19.3, -0.30, -0.025, m_asfalto)
caixa('rua_calcada', X0, X1, -19.3, -16.62, -0.30, 0.0, m_calcada)   # calcada junto ao muro/laje, topo = piso da laje
caixa('rua_meiofio', X0, X1, -19.5, -19.3, -0.30, 0.10, m_meiofio)
caixa('rua_calcada2', X0, X1, -33.8, -31.0, -0.30, 0.0, m_calcada)
caixa('rua_meiofio2', X0, X1, -31.2, -31.0, -0.30, 0.10, m_meiofio)

# postes de luz (neutros, sem vizinhos): somem junto com o chao
postes = []
m_poste = bpy.data.materials.new('poste'); m_poste.use_nodes = True
pp = m_poste.node_tree.nodes['Principled BSDF']; pp.inputs['Base Color'].default_value = (0.02, 0.02, 0.022, 1); pp.inputs['Metallic'].default_value = 0.6; pp.inputs['Roughness'].default_value = 0.4
m_lamp = bpy.data.materials.new('lampada'); m_lamp.use_nodes = True
pl = m_lamp.node_tree.nodes['Principled BSDF']; pl.inputs['Base Color'].default_value = (1, 0.7, 0.35, 1)
pl.inputs['Emission Color'].default_value = (1.0, 0.62, 0.25, 1); pl.inputs['Emission Strength'].default_value = 40
for px_ in (-2.4, 12.2):
    pole = caixa('poste', px_ - 0.07, px_ + 0.07, -19.9, -19.65, 0.0, 4.2, m_poste)
    braco = caixa('braco', px_ - 0.05, px_ + 0.05, -19.9 + (0.0), -19.7 + 0.0 + 0.0, 4.15, 4.25, m_poste)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.16, location=(px_, -19.77, 4.35))
    lamp = bpy.context.active_object; lamp.data.materials.append(m_lamp); lamp.visible_shadow = False
    ld = bpy.data.lights.new('poste_luz', 'POINT'); ld.energy = 2200; ld.color = (1.0, 0.62, 0.3); ld.shadow_soft_size = 0.25
    lo = bpy.data.objects.new('poste_luz', ld); sc.collection.objects.link(lo); lo.location = (px_, -19.77, 4.2)
    postes.append((pole, braco, lamp, lo, 2200.0))

SOMBRA = float(os.environ.get('INTRO_SOMBRA', '0.52'))   # opacidade maxima da sombra da laje (AgX escurece mais que o alfa sobre #0e1630 da pagina)
mr.inputs[3].default_value = SOMBRA
# ---------------------------------------------------------------- camera
cam3 = CENA['cam']
camd = bpy.data.cameras.new('cam'); camd.sensor_fit = 'VERTICAL'; camd.clip_start = 0.1; camd.clip_end = 600
camo = bpy.data.objects.new('cam', camd); sc.collection.objects.link(camo); sc.camera = camo
POS_F = b3(cam3['position']); TGT_F = b3(cam3['target']); FOV_F = cam3['fov'] * 0.92
# Cena 1: drone parado a ~6 m de altura num canto da rua, em diagonal, olhando POR CIMA do muro
# para os comodos acesos e a piscina (nao um muro liso de frente). Depois sobe/entra ate a camera da maquete.
P0 = Vector((-4.5, -25.0, 6.0))                # canto esquerdo da rua em frente ao lote (y<-16), 6 m de altura
P1 = Vector((-2.0, -19.0, 7.5))                # sobe devagar e avanca na diagonal, ainda por cima do muro
P2 = Vector((3.0, -17.0, 13.0))
P3 = POS_F
TG0 = Vector((8.0, -7.0, 0.6)); T3 = TGT_F     # mira o miolo do lote (comodos e piscina), nao o muro
FOV0 = 50.0
PARADO = 0.10                                  # primeiros 10% do voo: o drone paira quase parado

def poe(t):
    s = smooth(min(max((t - PARADO) / (1 - PARADO), 0.0), 1.0))
    pos = bez(P0, P1, P2, P3, s)
    tg = TG0.lerp(T3, smooth(min(1.0, s * 1.08)) if s < 1 else 1.0)
    camo.location = pos
    camo.rotation_euler = (tg - pos).to_track_quat('-Z', 'Y').to_euler()
    camd.angle = math.radians(FOV0 + (FOV_F - FOV0) * s)
    return pos, tg

LUZ_FIM = float(os.environ.get('INTRO_LUZ_FIM', '0.25'))   # fracao das luzes dos comodos no ultimo quadro: 0.25 ~ brilho do base.webp; 1.0 ~ noite.webp (tudo aceso)
orig_luz = [(o, o.data.energy) for lst in luzes.values() for o in lst]
orig_emi = [(p_, s_) for (o, p_, s_, rid) in emissivos]
orig_est = [(sol, sol.energy), (area, area.energy)]
agua_mats = [m for m in bpy.data.materials if m.name == 'agua' or m.name.startswith('agua.')]

def estado(t):
    # estudio (sol/area): entardecer fraco no inicio, cheio no fim (igual ao base.webp)
    ke = 0.35 + 0.65 * smooth((t - 0.30) / 0.65)
    for l_, e_ in orig_est: l_.energy = e_ * ke
    # luzes dos comodos: acesas na rua; apagam ate o fim para casar com base.webp (a pagina acende as suas)
    kl = 1.0 - (1.0 - LUZ_FIM) * smooth((t - 0.45) / 0.50)
    for o, e_ in orig_luz: o.data.energy = e_ * kl; o.hide_render = kl < 0.002
    for p_, s_ in orig_emi: p_.inputs['Emission Strength'].default_value = s_ * kl
    # agua: menos espelhada nos angulos rasantes durante o voo
    lvl = 0.8 - 0.62 * smooth(t / 0.2) * (1 - smooth((t - 0.72) / 0.26))
    for m in agua_mats:
        pw = m.node_tree.nodes.get('Principled BSDF')
        if pw: pw.inputs['Specular IOR Level'].default_value = lvl
    kval.outputs[0].default_value = smooth((t - 0.10) / 0.78)          # ceu escurece ate #0e1630
    g = 1.0 - smooth((t - 0.50) / 0.34)                                 # chao/rua somem
    for v in fade_nodes: v.outputs[0].default_value = g
    for pole, braco, lamp, lo, e in postes:
        lo.data.energy = e * g; vis = g > 0.001
        for o in (pole, braco, lamp, lo): o.hide_render = not vis
    return g

# ---------------------------------------------------------------- render
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = AMOSTRAS
sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.03
sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'
sc.cycles.max_bounces = 6; sc.cycles.diffuse_bounces = 3; sc.cycles.glossy_bounces = 3
sc.cycles.transmission_bounces = 6; sc.cycles.transparent_max_bounces = 12; sc.cycles.volume_bounces = 0
sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
sc.cycles.sample_clamp_indirect = 8
sc.render.threads_mode = 'AUTO'
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - High Contrast'; sc.view_settings.exposure = -0.5
sc.render.film_transparent = False
sc.render.resolution_x = RW; sc.render.resolution_y = RH; sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.color_mode = 'RGB'; sc.render.image_settings.quality = 82
sc.use_nodes = False

caminho = []
for i in range(I0, I1 + 1):
    t = (i - 1) / (NQ - 1) if NQ > 1 else 1.0
    pos, tg = poe(t); g = estado(t)
    if os.environ.get('INTRO_DBG'): print('DBG k', kval.outputs[0].default_value, [round(v,4) for v in mixk.inputs[7].default_value], 'mix fac', mixk.inputs[0].default_value, 'links', [(l.from_node.name, l.to_node.name, l.to_socket.name) for l in w.node_tree.links], 'world', sc.world.name, w.name)
    bpy.context.view_layer.update()
    caminho.append({'i': i, 't': round(t, 4), 'pos_blender': [round(v, 3) for v in pos], 'alvo': [round(v, 3) for v in tg], 'chao': round(g, 3)})
    sc.render.filepath = os.path.join(SAIDA, 'intro_%03d.jpg' % i)
    t_ = time.time(); bpy.ops.render.render(write_still=True)
    print('quadro %d/%d t=%.2f pos=%s %.1fs' % (i, NQ, t, [round(v, 1) for v in pos], time.time() - t_), flush=True)
json.dump({'quadros': NQ, 'res': [RW, RH], 'fundo_linear': FUNDO, 'caminho': caminho}, open(os.path.join(SAIDA, '..', 'caminho.json') if os.path.isdir(os.path.join(SAIDA, '..')) else os.path.join(SAIDA, 'caminho.json'), 'w'), indent=1)
print('TEMPO intro %.1fs (setup %.1fs)' % (time.time() - T0, T1 - T0))
