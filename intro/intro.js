/* Intro "voo ate a maquete" — casa-chefe-noite. Sem bibliotecas.
 *
 * Uso (ver README no final do arquivo / instrucoes de integracao):
 *   <link rel="stylesheet" href="intro/intro.css">
 *   <div id="casaIntro"></div>          <!-- logo ANTES da secao da maquete -->
 *   <script src="intro/intro.js"></script>
 *   <script>
 *     CasaIntro.init({
 *       el: '#casaIntro',
 *       pasta: 'intro/quadros/', prefixo: 'intro_', ext: '.jpg', quadros: 72, digitos: 3,
 *       titulo: 'Casa Chefe', subtitulo: '...', botao: 'Entrar na casa',
 *       alvo: '#rvStage',        // secao/elemento da maquete (logo apos o #casaIntro)
 *       alvoImg: '.base',        // (opcional) imagem base dentro do alvo: o ultimo quadro se encaixa nela
 *       comprimento: 4,          // quantas alturas de tela de rolagem dura o voo
 *       aoTerminar: () => {}     // chamado ao chegar na maquete (tambem evento 'casa-intro:end' no window)
 *     });
 *   </script>
 *
 * Como funciona: #casaIntro vira um espaco de rolagem (comprimento x 100vh). Um canvas fixo cobre a pagina e
 * desenha o quadro que corresponde ao progresso da rolagem (com mistura entre quadros vizinhos). Ao fim do
 * espaco, o alvo (maquete) esta exatamente no topo da tela; o ultimo quadro ja foi encaixado no retangulo da
 * imagem base e o canvas se dissolve, entregando a vez ao modo foto sem corte.
 * prefers-reduced-motion: nada e criado, a pagina abre direto na maquete.
 */
(function (global) {
  'use strict';
  var FUNDO = '#0e1630';
  var clamp = function (v, a, b) { return v < a ? a : v > b ? b : v; };
  var smooth = function (x) { x = clamp(x, 0, 1); return x * x * (3 - 2 * x); };
  var $ = function (s, r) { return typeof s === 'string' ? (r || document).querySelector(s) : s; };
  var mk = function (tag, cls, txt) { var e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };

  function init(opt) {
    opt = opt || {};
    var host = $(opt.el || '#casaIntro');
    if (!host || host.__ci) return host && host.__ci;
    var reduz = global.matchMedia && global.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var api = { progresso: 0, terminou: false, destroy: function () {} };
    if (reduz) { host.hidden = true; document.documentElement.classList.add('ci-done'); api.terminou = true; global.setTimeout(function () { fire('casa-intro:end', { reduzido: true }); if (opt.aoTerminar) opt.aoTerminar(); }, 0); return api; }

    var N = opt.quadros || 72, dig = opt.digitos || 3, ext = opt.ext || '.jpg';
    var pasta = opt.pasta || 'quadros/', pref = opt.prefixo || 'intro_';
    var len = opt.comprimento || 4;
    var alvo = opt.alvo ? $(opt.alvo) : host.nextElementSibling;
    var alvoImg = opt.alvoImg ? $(opt.alvoImg, alvo) : null;
    host.__ci = api;
    host.classList.add('ci-track'); host.style.setProperty('--ci-len', len);

    // ---------- DOM
    var fx = mk('div', 'ci-fixed'); fx.setAttribute('role', 'region'); fx.setAttribute('aria-label', 'Introducao: voo ate a maquete da casa');
    var cv = mk('canvas', 'ci-canvas'); cv.setAttribute('aria-hidden', 'true');
    var shade = mk('div', 'ci-shade');
    var txt = mk('div', 'ci-txt');
    txt.append(mk('p', 'ci-eyebrow', opt.sobretitulo || 'Maquete 3D'), mk('h1', 'ci-titulo', opt.titulo || 'Casa Chefe'),
      mk('p', 'ci-sub', opt.subtitulo || 'Do portao ate a ultima luz acesa.'));
    var btn = mk('button', 'ci-btn', opt.botao || 'Entrar na casa'); btn.type = 'button'; txt.append(btn);
    var dica = mk('div', 'ci-dica', opt.dica || 'role para entrar');
    var pular = mk('button', 'ci-pular', opt.pular || 'Pular'); pular.type = 'button';
    var carga = mk('div', 'ci-carga');
    fx.append(cv, shade, txt, dica, pular, carga);
    document.body.appendChild(fx);
    var ctx = cv.getContext('2d', { alpha: false });

    // ---------- quadros (pre-carga progressiva)
    var imgs = new Array(N), ok = new Array(N), carregados = 0, W0 = 1280, H0 = 800;
    var nome = function (i) { var s = String(i + 1); while (s.length < dig) s = '0' + s; return pasta + pref + s + ext; };
    function ordem() {
      var o = [0, N - 1], vis = {0: 1}; vis[N - 1] = 1;
      [12, 6, 3, 2, 1].forEach(function (st) { for (var i = 0; i < N; i += st) if (!vis[i]) { vis[i] = 1; o.push(i); } });
      return o;
    }
    var fila = ordem(), ativos = 0;
    var lento = (navigator.connection && (navigator.connection.saveData || /2g/.test(navigator.connection.effectiveType || ''))) || false;
    var MAXPAR = lento ? 1 : (global.innerWidth < 760 ? 3 : 5);
    function carregaProx() {
      while (ativos < MAXPAR && fila.length) {
        (function (i) {
          var im = new Image(); im.decoding = 'async'; ativos++;
          im.onload = function () { imgs[i] = im; ok[i] = true; carregados++; ativos--; if (i === 0) { W0 = im.naturalWidth; H0 = im.naturalHeight; } carga.style.transform = 'scaleX(' + (carregados / N) + ')'; if (carregados === N) carga.style.opacity = 0; sujo = true; pedeQuadro(); carregaProx(); };
          im.onerror = function () { ativos--; carregaProx(); };
          im.src = nome(i);
        })(fila.shift());
      }
    }
    carregaProx();

    // ---------- desenho
    var sujo = true, rafId = 0, cw = 0, ch = 0, dpr = 1, ultimoDesenho = -1;
    function medir() {
      dpr = Math.min(global.devicePixelRatio || 1, 1.5);
      var w = global.innerWidth, h = global.innerHeight;
      var cap = 1800 / Math.max(w, h) ; if (cap < dpr) dpr = cap;     // limita pixels no celular/telas grandes
      cw = Math.round(w * dpr); ch = Math.round(h * dpr);
      if (cv.width !== cw || cv.height !== ch) { cv.width = cw; cv.height = ch; }
      sujo = true;
    }
    function maisProximo(i, dir) { // quadro carregado mais perto de i
      for (var d = 0; d < N; d++) { var a = i - d, b = i + d; if (a >= 0 && ok[a]) return a; if (b < N && ok[b]) return b; }
      return -1;
    }
    var amostra = mk('canvas'); amostra.width = amostra.height = 1; var actx = amostra.getContext('2d', { willReadFrequently: true });
    function cor(im, topo) {
      try { actx.drawImage(im, 0, topo ? 0 : im.naturalHeight - 6, im.naturalWidth, 6, 0, 0, 1, 1); var d = actx.getImageData(0, 0, 1, 1).data; return 'rgb(' + d[0] + ',' + d[1] + ',' + d[2] + ')'; } catch (e) { return FUNDO; }
    }
    function rectFinal() { // onde o ultimo quadro deve cair (retangulo da imagem base com o alvo no topo da tela)
      if (!alvo) return null;
      var ar = alvo.getBoundingClientRect(), ir = (alvoImg || alvo).getBoundingClientRect();
      if (!ir.width) return null;
      return { x: ir.left, y: ir.top - ar.top, w: ir.width, h: ir.height };
    }
    function desenha(p) {
      var vw = cw / dpr, vh = ch / dpr, e = smooth((p - 0.80) / 0.19);       // encaixe final: 80% -> 99%
      // retangulo "cobrir" (cover) com leve ancoragem; em retrato, encaixa pela largura
      var ar = W0 / H0, sc = Math.max(vw / W0, vh / H0), rc;
      if (vw / vh < 0.9) sc = Math.max(vw / (W0 * 0.96), 0.0001);           // retrato: mostra quase a casa toda de largura
      rc = { w: W0 * sc, h: H0 * sc }; rc.x = (vw - rc.w) / 2; rc.y = (vh - rc.h) / 2;
      var rf = e > 0 ? rectFinal() : null, R = rc;
      if (rf) R = { x: rc.x + (rf.x - rc.x) * e, y: rc.y + (rf.y - rc.y) * e, w: rc.w + (rf.w - rc.w) * e, h: rc.h + (rf.h - rc.h) * e };
      var f = p * (N - 1), i0 = Math.floor(f), t = f - i0, i1 = Math.min(N - 1, i0 + 1);
      var a = ok[i0] ? i0 : maisProximo(i0), b = ok[i1] ? i1 : maisProximo(i1);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      if (a < 0) { ctx.fillStyle = FUNDO; ctx.fillRect(0, 0, vw, vh); return; }
      var A = imgs[a];
      // faixas fora do quadro (retrato / encaixe final): cor de cima/baixo do quadro atual
      if (R.x > 0.5 || R.y > 0.5 || R.x + R.w < vw - 0.5 || R.y + R.h < vh - 0.5) {
        var g = ctx.createLinearGradient(0, 0, 0, vh); g.addColorStop(0, cor(A, true)); g.addColorStop(1, cor(A, false));
        ctx.fillStyle = g; ctx.fillRect(0, 0, vw, vh);
        if (e > 0.5) { ctx.globalAlpha = (e - 0.5) * 2; ctx.fillStyle = FUNDO; ctx.fillRect(0, 0, vw, vh); ctx.globalAlpha = 1; }
      }
      ctx.imageSmoothingQuality = 'high';
      ctx.globalAlpha = 1; ctx.drawImage(A, R.x, R.y, R.w, R.h);
      if (b >= 0 && b !== a && t > 0.02) { ctx.globalAlpha = smooth(t); ctx.drawImage(imgs[b], R.x, R.y, R.w, R.h); ctx.globalAlpha = 1; }
    }

    // ---------- progresso / rolagem
    var p = 0, fim = false;
    function leP() {
      var topo = host.getBoundingClientRect().top + (global.pageYOffset || document.documentElement.scrollTop);
      var total = host.offsetHeight;                      // rolagem total do voo
      return clamp(((global.pageYOffset || document.documentElement.scrollTop) - topo) / total, 0, 1);
    }
    function atualiza() {
      rafId = 0;
      var np = leP();
      if (np !== p) { p = np; sujo = true; }
      api.progresso = p;
      var visivel = p < 0.9995;
      if (sujo) {
        sujo = false;
        if (visivel) desenha(p);
        // titulo some cedo; tudo se dissolve no fim
        var tt = smooth(p / 0.10);
        txt.style.opacity = 1 - tt; txt.style.transform = 'translateY(' + (-tt * 28).toFixed(1) + 'px)';
        txt.style.visibility = tt >= 1 ? 'hidden' : '';
        dica.style.opacity = 0.8 * (1 - smooth(p / 0.04)); pular.style.opacity = 1 - smooth((p - 0.9) / 0.08);
        fx.style.opacity = 1 - smooth((p - 0.985) / 0.015);
        fx.classList.toggle('ci-off', !visivel);
        global.dispatchEvent(new CustomEvent('casa-intro:progresso', { detail: { p: p } }));
      }
      if (visivel && fim) { fim = false; api.terminou = false; document.documentElement.classList.remove('ci-done'); fire('casa-intro:volta'); }
      if (!visivel && !fim) { fim = true; api.terminou = true; document.documentElement.classList.add('ci-done'); fire('casa-intro:end', {}); if (opt.aoTerminar) try { opt.aoTerminar(); } catch (e) { console.error(e); } }
    }
    function pedeQuadro() { if (!rafId) rafId = global.requestAnimationFrame(atualiza); }
    function fire(n, d) { global.dispatchEvent(new CustomEvent(n, { detail: d || {} })); }

    // ---------- botao / pular: rolagem animada (cancela se a pessoa mexer)
    var anim = 0;
    function vaiPara(y, dur) {
      var y0 = global.pageYOffset, t0 = performance.now(); global.cancelAnimationFrame(anim);
      function passo(now) {
        var k = clamp((now - t0) / dur, 0, 1), e = k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
        global.scrollTo(0, y0 + (y - y0) * e);
        if (k < 1) anim = global.requestAnimationFrame(passo);
      }
      anim = global.requestAnimationFrame(passo);
    }
    var cancela = function () { global.cancelAnimationFrame(anim); };
    ['wheel', 'touchstart', 'keydown', 'mousedown'].forEach(function (ev) { global.addEventListener(ev, cancela, { passive: true }); });
    var fimY = function () { return host.getBoundingClientRect().top + (global.pageYOffset || 0) + host.offsetHeight; };
    btn.addEventListener('click', function () { vaiPara(fimY(), 1000 + len * 900); });
    pular.addEventListener('click', function () { cancela(); global.scrollTo(0, fimY()); });

    global.addEventListener('scroll', pedeQuadro, { passive: true });
    global.addEventListener('resize', function () { medir(); pedeQuadro(); });
    global.addEventListener('orientationchange', function () { global.setTimeout(function () { medir(); pedeQuadro(); }, 250); });
    medir(); atualiza();
    // quando a imagem base do alvo carregar, o retangulo final muda: redesenha
    if (alvoImg) alvoImg.addEventListener('load', function () { sujo = true; pedeQuadro(); });
    api.destroy = function () { fx.remove(); host.classList.remove('ci-track'); delete host.__ci; };
    return api;
  }

  global.CasaIntro = { init: init };
})(window);
