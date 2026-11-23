"""Gera intro/quadros_m (1280x800, celular) reduzindo os quadros 1920x1200 de intro/quadros com Lanczos.
Reduzir o render grande sai mais nitido que renderizar de novo a 1280x800, e nao custa tempo de Blender.
Uso: python render/quadros_celular.py [ORIGEM] [DESTINO]"""
import sys, os, glob
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, '..', 'intro', 'quadros')
dst = sys.argv[2] if len(sys.argv) > 2 else os.path.join(AQUI, '..', 'intro', 'quadros_m')
os.makedirs(dst, exist_ok=True)
fs = sorted(glob.glob(os.path.join(src, 'intro_*.jpg')))
TESTE = os.environ.get('RENDER_TESTE') == '1'
assert TESTE or len(fs) == 72, len(fs)
for f in fs:
    im = Image.open(f).convert('RGB')
    assert TESTE or im.size == (1920, 1200), (f, im.size)
    im.resize((1280, 800) if not TESTE else (im.size[0] * 2 // 3, im.size[1] * 2 // 3), Image.LANCZOS).save(os.path.join(dst, os.path.basename(f)), quality=88, optimize=True, progressive=True)
print('ok', len(fs), 'quadros ->', os.path.abspath(dst))
