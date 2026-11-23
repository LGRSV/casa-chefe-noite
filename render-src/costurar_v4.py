"""Costura as faixas da maquete (montar_v4.py main com STRIP=k/n) e aplica o pos: saturacao, brilho (glare) nas luzes, vinheta.
Uso: python render/costurar_v4.py PASTA_FAIXAS N PASTA_SAIDA
  PASTA_FAIXAS contem s0..s{N-1} (cada uma saida do montar_v4 com STRIP=k/N) -> PASTA_SAIDA/base.png, <comodo>.png, noite.png, pontos.json
Por que faixas: o PC tem pouca RAM; 2880x1800 com 12 passes de luz estoura a memoria (swap = 10x mais lento).
Cada faixa tem 48 px de sobreposicao, misturada em rampa na costura."""
import sys, os, json, glob, shutil
import numpy as np
from PIL import Image, ImageFilter

pasta, N, saida = sys.argv[1], int(sys.argv[2]), sys.argv[3]
os.makedirs(saida, exist_ok=True)
SAT = float(os.environ.get('SAT', '1.04'))
VIG = float(os.environ.get('VIG', '0.22'))
GLARE_K = float(os.environ.get('GLARE_K', '0.3'))
OV = 48

def le(p):
    return np.asarray(Image.open(p).convert('RGBA'), dtype=np.float32) / 255.0

nomes = [os.path.basename(f)[:-4] for f in glob.glob(os.path.join(pasta, 's0', '*.png'))]
nomes = [n for n in nomes if n != 'frame_tmp']
meta = [json.load(open(os.path.join(pasta, 's%d' % k, 'faixa.json'))) for k in range(N)]
H = meta[0]['H']

def vinheta(h, w):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((xx / w - 0.5) / 0.62) ** 2 + ((yy / h - 0.5) / 0.60) ** 2)   # 0 centro, ~1 cantos
    t = np.clip((r - 0.45) / 0.65, 0, 1); t = t * t * (3 - 2 * t)
    return (1.0 - VIG * t)[..., None]

for nome in sorted(nomes):
    W = Image.open(os.path.join(pasta, 's0', nome + '.png')).size[0]
    acc = np.zeros((H, W, 4), np.float32); peso = np.zeros((H, W, 1), np.float32)
    for k in range(N):
        a = le(os.path.join(pasta, 's%d' % k, nome + '.png')); y0, y1 = meta[k]['y0'], meta[k]['y1']
        assert a.shape[0] == y1 - y0, (nome, k, a.shape, y0, y1)
        w = np.ones((a.shape[0], 1, 1), np.float32)
        if k > 0: w[:2 * OV, 0, 0] = np.linspace(0, 1, 2 * OV)
        if k < N - 1: w[-2 * OV:, 0, 0] = np.minimum(w[-2 * OV:, 0, 0], np.linspace(1, 0, 2 * OV))
        acc[y0:y1] += a * w; peso[y0:y1] += w
    img = acc / np.maximum(peso, 1e-6)
    rgb, al = img[..., :3], img[..., 3:]
    luma = (rgb * np.array([0.2126, 0.7152, 0.0722], np.float32)).sum(-1, keepdims=True)
    rgb = np.clip(luma + (rgb - luma) * SAT, 0, 1)
    if nome != 'base':   # brilho suave so nas luzes
        br = np.clip((rgb.max(-1, keepdims=True) - 0.90) / 0.1, 0, 1) * rgb
        small = Image.fromarray((br * 255).astype(np.uint8)).resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(5))
        glow = np.asarray(small.resize((W, H), Image.BILINEAR), dtype=np.float32) / 255.0
        rgb = np.clip(rgb + GLARE_K * glow, 0, 1)
    rgb = rgb * vinheta(H, W)
    out = np.concatenate([rgb, al], -1)
    Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGBA').save(os.path.join(saida, nome + '.png'), compress_level=9)
    print('ok', nome, flush=True)
shutil.copy(os.path.join(pasta, 's0', 'pontos.json'), os.path.join(saida, 'pontos.json'))
