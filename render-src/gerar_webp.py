"""Gera as imagens da pagina a partir do render final (SEM curva de gama: a base v4 ja sai exposta pela luz).
Uso: python render/gerar_webp.py PASTA_MAQUETE PASTA_GIRO
  PASTA_MAQUETE: saida do costurar_v4.py (base.png, <comodo>.png, noite.png, pontos.json, 2880x1800)
  PASTA_GIRO:    saida do montar_v4.py giro (giro_01..08.jpg, 1920x1200)
Grava em render/web/: <nome>.webp (qualidade 90, RGBA quando a imagem tem alfa), giro_NN.jpg (copia sem ampliar)
e confere os pontos (xr, yr) contra o PTS da pagina."""
import sys, os, glob, json, shutil
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
WEB = os.environ.get('WEB_OUT') or os.path.join(AQUI, 'web')
TESTE = os.environ.get('RENDER_TESTE') == '1'
maq, giro = sys.argv[1], sys.argv[2]
os.makedirs(WEB, exist_ok=True)

for f in sorted(glob.glob(os.path.join(maq, '*.png'))):
    n = os.path.basename(f)[:-4]
    im = Image.open(f)
    im = im.convert('RGBA') if 'A' in im.getbands() else im.convert('RGB')
    assert TESTE or im.size == (2880, 1800), (n, im.size)
    im.save(os.path.join(WEB, n + '.webp'), 'WEBP', quality=90, method=6)
    print('webp', n, im.mode, im.size, flush=True)

gs = sorted(glob.glob(os.path.join(giro, 'giro_*.jpg')))
assert TESTE or len(gs) == 8, gs
for g in gs:
    assert TESTE or Image.open(g).size == (1920, 1200), g
    shutil.copy(g, os.path.join(WEB, os.path.basename(g)))
print('giro', len(gs), 'quadros 1920x1200')

p = json.load(open(os.path.join(maq, 'pontos.json'), encoding='utf-8'))
print('pontos', p['largura'], 'x', p['altura'])
print('  ' + ', '.join("%s: [%.4f, %.4f, '%s']" % (k, v['xr'], v['yr'], v['label']) for k, v in p['pontos'].items()))
