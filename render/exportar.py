"""Exporta a cena do index.html (servido em localhost:8765) para render/casa.glb + render/cena.json.
Uso: na raiz do repo, `python -m http.server 8765` e depois `python render/exportar.py`."""
import json, base64, os, urllib.request, urllib.parse
from playwright.sync_api import sync_playwright
OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(OUT)
TV = 'https://cdn.jsdelivr.net/npm/three@0.170.0'
EXP = TV + '/examples/jsm/exporters/GLTFExporter.js'
THREE = TV + '/build/three.module.min.js'

def route(r):
    u = r.request.url
    if u.startswith(TV + '/examples/jsm/'):
        t = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'x'})).read().decode()
        t = t.replace("from 'three'", "from '%s'" % THREE).replace('from "three"', 'from "%s"' % THREE)
        r.fulfill(body=t, content_type='application/javascript', headers={'access-control-allow-origin': '*'})
    elif u.startswith('http://localhost:8765/'):
        import mimetypes
        pth = os.path.join(ROOT, urllib.parse.unquote(u.split('?')[0][len('http://localhost:8765/'):]) or 'index.html')
        if os.path.isfile(pth):
            r.fulfill(body=open(pth, 'rb').read(), content_type=mimetypes.guess_type(pth)[0] or 'application/octet-stream')
        else:
            r.fulfill(status=404, body='')
    else:
        r.continue_()

JS = """async ()=>{
const c=document.querySelector('casa3d-card'), sc=c._scene;
const THREE=await import('%(THREE)s');
const {GLTFExporter}=await import('%(EXP)s');
c._orbit.userAt=performance.now()+1e12; c._resetView(false);
await new Promise(r=>setTimeout(r,2500));
const lights=[];
for(const [key,rt] of c._items){ if(!rt.lights) continue; const its=c._roomsAll().filter(r=>c._roomKeys(r).includes(key));
  for(const {L,i} of rt.lights){ const p=L.position; let r=null;
    if(its.length===1) r=its[0]; else { r=c._roomAt(p.x,p.z); if(r&&!its.includes(r)) r=its.find(q=>q.rects.some(([x,z,w,d])=>p.x>=x-.8&&p.x<=x+w+.8&&p.z>=z-.8&&p.z<=z+d+.8))||its[0]; }
    lights.push({item:key,room:r?r.id:null,type:L.type,pos:[p.x,p.y,p.z],color:rt.color.getHex(),i:i,distance:L.distance,decay:L.decay}); } }
const st=c.casa3d.state(); const defOn=Object.keys(st.devices).filter(k=>st.devices[k]);
const rooms=c._roomsAll().map(r=>{const b=c._roomBox(r);return {id:r.id,label:r.label,items:c._roomKeys(r),box:b,center:[(b[0]+b[2])/2,1.2,(b[1]+b[3])/2]}});
const cam={position:c._camera.position.toArray(),target:c._orbit.target.toArray(),fov:c._camera.fov,aspect:c._camera.aspect,near:c._camera.near,far:c._camera.far};
const hide=(o)=>{o.visible=false;}; let nAgua=0, nHalo=0;
sc.traverse(o=>{ if(o.isSprite||o.isLight){hide(o);return;}
  if(o.isMesh&&!o.isInstancedMesh){ const m=o.material;
    if(m.isShaderMaterial){ o.material=new THREE.MeshStandardMaterial({color:0x22c8d6,transparent:true,opacity:0.7,roughness:0.1,name:'agua'}); nAgua++; }
    else if(m.isMeshBasicMaterial&&(m.transparent||m.blending===THREE.AdditiveBlending)){ hide(o); nHalo++; } } });
if(c._hl) hide(c._hl); if(c._mk) hide(c._mk);
for(const s of [c._skyNight,c._skyDay,c._skyDusk]) if(s) hide(s);
sc.background=null; sc.fog=null; sc.environment=null;
const inst=[]; sc.traverse(o=>{ if(o.isInstancedMesh&&o.visible) inst.push(o);}); let nInst=0;
for(const o of inst){ const g=new THREE.Group(); const m4=new THREE.Matrix4(); const col=new THREE.Color();
  for(let k=0;k<o.count;k++){ o.getMatrixAt(k,m4); let mat=o.material; if(o.instanceColor){o.getColorAt(k,col); mat=o.material.clone(); mat.color.multiply(col);} const mm=new THREE.Mesh(o.geometry,mat); mm.applyMatrix4(m4); g.add(mm); nInst++; }
  o.parent.add(g); g.applyMatrix4(o.matrix); o.visible=false; }
const glb=await new Promise((res,rej)=>new GLTFExporter().parse(sc,res,rej,{binary:true,onlyVisible:true}));
const u8=new Uint8Array(glb); let s=''; for(let k=0;k<u8.length;k+=32768) s+=String.fromCharCode.apply(null,u8.subarray(k,k+32768));
return {glb:btoa(s),lights,defOn,rooms,cam,info:{nAgua,nHalo,nInst}}; }""" % {'THREE': THREE, 'EXP': EXP}

with sync_playwright() as p:
    b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    ctx = b.new_context(viewport={'width': 1600, 'height': 1000})
    ctx.route('**/*', route)
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: print('PAGEERR', e))
    pg.on('console', lambda m: print('CONSOLE', m.text) if m.type == 'error' else None)
    pg.goto('http://localhost:8765/index.html')
    pg.wait_for_timeout(20000)  # espera o carro carregar
    r = pg.evaluate(JS)
    open(os.path.join(OUT, 'casa.glb'), 'wb').write(base64.b64decode(r.pop('glb')))
    json.dump(r, open(os.path.join(OUT, 'cena.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('glb', os.path.getsize(os.path.join(OUT, 'casa.glb')), 'luzes', len(r['lights']), r['info'], r['cam'])
    b.close()
