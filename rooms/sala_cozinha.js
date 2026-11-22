function roomSalaCozinha(ctx) {
  // ---------------------------------------------------------------------------
  // SALA (x 6,8–10,3) + COZINHA (x 10,3–12,5), integradas (sem divisória) · z 0–4,2
  // Estilo minimalista (referência de vídeo): creme/linho, carvalho, nogueira, pedra clara, preto fosco,
  // verde-oliva/sálvia e terracota em detalhe. Layout e posições da casa real preservados.
  // Objetos do cartão (ar-condicionado, pendentes) NÃO são recriados.
  // ---------------------------------------------------------------------------
  const THREE = ctx.THREE, M = ctx.M, F = ctx.F;
  const box = (...a) => ctx.box(...a), cyl = (...a) => ctx.cyl(...a), sph = (...a) => ctx.sph(...a);
  const place = (...a) => ctx.place(...a), std = (o) => ctx.std(o), rnd = () => ctx.rnd();
  const put = (m) => { ctx.add(m); return m; };
  const G = () => new THREE.Group();
  const rot = (m, x = 0, y = 0, z = 0) => { m.rotation.set(x, y, z); return m; };
  const mesh = (geo, mat, x, y, z) => { const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.castShadow = true; m.receiveShadow = true; return m; };
  // caixa com os 4 cantos verticais arredondados (raio r); origem no centro
  const rb = (w, h, d, mat, x, y, z, r = 0.04, opts = {}) => {
    r = Math.min(r, w * 0.49, d * 0.49);
    const s = new THREE.Shape(), hw = w / 2, hd = d / 2;
    s.moveTo(-hw + r, -hd); s.lineTo(hw - r, -hd); s.absarc(hw - r, -hd + r, r, -Math.PI / 2, 0, false);
    s.lineTo(hw, hd - r); s.absarc(hw - r, hd - r, r, 0, Math.PI / 2, false);
    s.lineTo(-hw + r, hd); s.absarc(-hw + r, hd - r, r, Math.PI / 2, Math.PI, false);
    s.lineTo(-hw, -hd + r); s.absarc(-hw + r, -hd + r, r, Math.PI, Math.PI * 1.5, false);
    const g = new THREE.ExtrudeGeometry(s, { depth: h, bevelEnabled: false, curveSegments: 5 });
    g.rotateX(-Math.PI / 2); g.translate(0, -h / 2, 0);
    const m = new THREE.Mesh(g, mat); m.position.set(x, y, z);
    m.castShadow = opts.cast !== false; m.receiveShadow = true; return m;
  };

  // Materiais locais (nunca altera os materiais compartilhados M.*)
  const walnut   = std({ color: 0x5b3d29, roughness: 0.55 });
  const walnutDk = std({ color: 0x3f2a1c, roughness: 0.55 });
  const oak      = std({ color: 0xcaa878, roughness: 0.6 });
  const oakBack  = std({ color: 0xcaa878, roughness: 0.6 }); oakBack.side = THREE.DoubleSide;
  const olive    = std({ color: 0x6b7040, roughness: 0.92 });
  const sage     = std({ color: 0x9aa58a, roughness: 0.92 });
  const terra    = std({ color: 0xb5623f, roughness: 0.9 });
  const cream    = std({ color: 0xe6ddcb, roughness: 0.95 });
  const creamLt  = std({ color: 0xf1ebdd, roughness: 0.95 });
  const drape    = std({ color: 0xece5d6, roughness: 1 });
  const sheer    = std({ color: 0xffffff, roughness: 1, transparent: true, opacity: 0.3 });
  const glassy   = std({ color: 0xa9bcc4, roughness: 0.15, metalness: 0.1, transparent: true, opacity: 0.5 });
  const marble   = std({ color: 0xece8de, roughness: 0.22, metalness: 0.02 });   // bancada de pedra clara
  const stoneDk  = std({ color: 0x2a2d2c, roughness: 0.3 });
  const ceramic  = std({ color: 0xf1ece2, roughness: 0.5 });
  const wicker   = std({ color: 0xb9925a, roughness: 0.95 });
  const black    = std({ color: 0x151515, roughness: 0.55 });                   // preto fosco
  const inox     = std({ color: 0xc9cdd0, roughness: 0.32, metalness: 0.65 });
  const paper    = std({ color: 0xfbfaf5, roughness: 0.9 });
  const led      = std({ color: 0xffd9a0, emissive: 0xffa94d, emissiveIntensity: 1.5 });   // fita LED âmbar
  const fruit    = [std({ color: 0xd98a3a, roughness: 0.7 }), std({ color: 0x9ab84a, roughness: 0.7 }), std({ color: 0xb8523a, roughness: 0.7 }), std({ color: 0xe6c84a, roughness: 0.8 })];
  const woodMed = oak, mustard = terra, linen = cream;   // nomes antigos -> paleta nova

  // ======================= BUILDERS (origem no centro da base) =======================
  // Rack de nogueira 1,6 m flutuante: frentes lisas, vão recuado escuro com fita LED embaixo
  const rack = () => {
    const g = G();
    g.add(box(1.5, 0.08, 0.36, black, 0, 0.14, 0));                                        // recuo escuro (parece flutuar)
    g.add(rb(1.6, 0.4, 0.42, walnut, 0, 0.36, 0, 0.02));
    g.add(box(1.62, 0.025, 0.44, oak, 0, 0.5725, 0));                                      // tampo carvalho fino
    for (const sx of [-1, 1]) g.add(box(0.76, 0.34, 0.012, walnutDk, sx * 0.39, 0.36, 0.216));   // frentes lisas (push)
    g.add(box(0.012, 0.34, 0.014, black, 0, 0.36, 0.217));                                 // fresta central
    g.add(box(1.5, 0.012, 0.012, led, 0, 0.105, 0.17, { cast: false }));                   // LED sob o rack
    return g;
  };
  // TV fina com moldura preta (tela para +z), pé central escondido
  const tv = () => {
    const g = G();
    g.add(box(0.28, 0.012, 0.14, black, 0, 0.006, 0));
    g.add(box(0.05, 0.1, 0.02, black, 0, 0.055, 0));
    g.add(box(0.74, 0.44, 0.022, black, 0, 0.32, 0));
    g.add(box(0.71, 0.41, 0.006, M.screenOff, 0, 0.32, 0.014, { cast: false }));
    return g;
  };
  // Sofá baixo de linho creme, formas macias, sem pés aparentes (encosto em -z)
  const sofa = () => {
    const g = G();
    g.add(box(1.28, 0.06, 0.66, black, 0, 0.03, 0));                                       // plinto recuado
    g.add(rb(1.42, 0.26, 0.84, cream, 0, 0.19, 0, 0.1));                                   // base
    g.add(rb(1.42, 0.34, 0.2, cream, 0, 0.5, -0.31, 0.08));                                // encosto baixo
    for (const sx of [-1, 1]) {
      g.add(rb(0.17, 0.2, 0.84, cream, sx * 0.62, 0.43, 0, 0.07));                         // braços arredondados
      g.add(rb(0.52, 0.11, 0.58, creamLt, sx * 0.27, 0.375, 0.07, 0.07));                  // almofada do assento
    }
    g.add(rot(rb(0.4, 0.34, 0.1, sage, -0.36, 0.56, -0.12, 0.06), -0.15, 0.2));           // almofadas sálvia / terracota
    g.add(rot(rb(0.34, 0.3, 0.1, terra, 0.4, 0.55, -0.12, 0.05), -0.12, -0.2));
    return g;
  };
  // Poltrona arredondada verde-oliva (frente em +z)
  const armchair = () => {
    const g = G();
    const oliveBack = olive.clone(); oliveBack.side = THREE.DoubleSide;
    g.add(cyl(0.3, 0.3, 0.3, olive, 0, 0.16, 0, 24));
    g.add(mesh(new THREE.CylinderGeometry(0.3, 0.3, 0.3, 24, 1, true, Math.PI * 0.3, Math.PI * 1.4), oliveBack, 0, 0.45, 0));
    g.add(cyl(0.24, 0.24, 0.07, sage, 0, 0.33, 0.03, 24));                                // almofada do assento
    g.add(cyl(0.2, 0.2, 0.05, black, 0, 0.015, 0, 18));
    return g;
  };
  // Mesa de centro redonda de pedra com base de carvalho
  const coffeeTable = () => {
    const g = G();
    g.add(cyl(0.3, 0.3, 0.03, marble, 0, 0.36, 0, 32));
    g.add(cyl(0.16, 0.2, 0.34, oak, 0, 0.17, 0, 24));
    // 22/11: removido a pedido do João (vasinho com ramo na mesa de centro)
    return g;
  };
  // Cadeira de jantar: carvalho claro, assento com almofada fina, pernas pretas finas (encosto em -z)
  const chair = () => {
    const g = G();
    g.add(rb(0.44, 0.035, 0.44, oak, 0, 0.445, 0, 0.06));
    g.add(rb(0.38, 0.03, 0.38, sage, 0, 0.478, 0.01, 0.06));
    for (const [sx, sz] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) g.add(cyl(0.011, 0.011, 0.43, black, sx * 0.19, 0.215, sz * 0.19, 6));
    g.add(mesh(new THREE.CylinderGeometry(0.33, 0.33, 0.34, 14, 1, true, Math.PI - 0.62, 1.24), oakBack, 0, 0.665, 0.12));
    return g;
  };
  // Mesa oval 1,5 × 0,95: tampo de carvalho fino, pernas pretas finas
  const table = () => {
    const g = G();
    const top = cyl(1, 1, 0.035, oak, 0, 0.76, 0, 48); top.scale.set(0.75, 1, 0.475); g.add(top);
    for (const [sx, sz] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) g.add(cyl(0.016, 0.013, 0.74, black, sx * 0.5, 0.37, sz * 0.25, 8));
    g.add(box(1.0, 0.03, 0.02, black, 0, 0.72, 0)); g.add(box(0.02, 0.03, 0.46, black, -0.5, 0.72, 0)); g.add(box(0.02, 0.03, 0.46, black, 0.5, 0.72, 0));
    return g;
  };
  // Centro de mesa: caminho de linho + fruteira de cerâmica (posicionar a y = tampo)
  const tableTop = () => {
    const g = G();
    g.add(box(0.9, 0.004, 0.28, cream, 0, 0.002, 0, { cast: false }));
    g.add(cyl(0.12, 0.08, 0.05, ceramic, 0, 0.025, 0, 24));
    g.add(sph(0.04, fruit[1], -0.04, 0.065, 0.02)); g.add(sph(0.04, fruit[0], 0.045, 0.065, -0.03)); g.add(sph(0.036, fruit[2], 0.005, 0.098, 0));
    // 22/11: removido a pedido do João (vasinho com ramo no centro de mesa)
    return g;
  };
  // Banqueta alta: assento arredondado oliva, pernas pretas finas
  const stool = () => {
    const g = G();
    g.add(cyl(0.17, 0.17, 0.05, olive, 0, 0.705, 0, 28));
    for (let i = 0; i < 3; i++) { const a = (i * Math.PI * 2) / 3 + Math.PI / 6; g.add(cyl(0.01, 0.01, 0.68, black, Math.cos(a) * 0.12, 0.34, Math.sin(a) * 0.12, 6)); }
    g.add(cyl(0.12, 0.12, 0.012, black, 0, 0.3, 0, 18));
    return g;
  };
  // Geladeira inox embutida (frente em +z): painéis lisos, puxadores finos e longos, sem ímãs
  const fridge = () => {
    const g = G();
    g.add(box(0.72, 0.08, 0.66, black, 0, 0.04, 0));
    g.add(rb(0.75, 1.77, 0.7, inox, 0, 0.965, 0, 0.012));
    g.add(box(0.73, 0.01, 0.01, black, 0, 1.3, 0.352));
    g.add(box(0.014, 0.55, 0.022, black, -0.3, 1.58, 0.364));
    g.add(box(0.014, 0.9, 0.022, black, -0.3, 0.78, 0.364));
    return g;
  };
  // 22/11: removido a pedido do João (planta alta em vaso)
  // Fogão: cooktop de vidro preto + forno inox embutido (frente em +z)
  const stove = () => {
    const g = G();
    g.add(box(0.5, 0.05, 0.5, black, 0, 0.025, 0));
    g.add(rb(0.58, 0.81, 0.58, inox, 0, 0.455, 0, 0.01));
    g.add(box(0.6, 0.016, 0.6, black, 0, 0.868, 0));
    for (const [sx, sz] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) g.add(cyl(0.07, 0.07, 0.004, stoneDk, sx * 0.14, 0.878, sz * 0.14, 20));
    g.add(box(0.5, 0.36, 0.012, black, 0, 0.36, 0.294));
    g.add(box(0.36, 0.14, 0.008, M.screenOff, 0, 0.4, 0.302, { cast: false }));
    g.add(box(0.46, 0.014, 0.02, inox, 0, 0.57, 0.31));
    g.add(box(0.5, 0.06, 0.012, black, 0, 0.73, 0.294));
    for (let i = 0; i < 4; i++) g.add(rot(cyl(0.011, 0.011, 0.02, inox, -0.18 + i * 0.12, 0.73, 0.305, 10), Math.PI / 2));
    return g;
  };
  // Quadro-textura minimalista na parede do fundo (z = 0)
  const frame = (w, h, x, y, art) => {
    put(box(w, h, 0.025, art, x, y, 0.09));
    put(box(w - 0.1, h - 0.1, 0.006, creamLt, x, y, 0.1, { cast: false }));
  };

  // ======================= SALA (x 6,8–10,3) =======================
  // Rack flutuante com TV fina e objetos; fita LED no nicho (AC do cartão fica mais alto, y 2,2–2,5)
  place(rack(), 7.76, 0.31);
  place(tv(), 7.76, 0.31, 0, 0.585);
  // 22/11: removido a pedido do João (vaso de cerâmica com ramos secos)
  put(box(0.2, 0.03, 0.15, cream, 8.36, 0.6, 0.31));                                             // livros
  put(rot(box(0.18, 0.03, 0.14, terra, 8.36, 0.63, 0.31), 0, 0.15, 0));
  put(cyl(0.05, 0.05, 0.02, black, 8.36, 0.655, 0.31, 20));                                      // tigela preta
  frame(0.7, 0.5, 7.76, 1.5, cream); frame(0.34, 0.46, 8.4, 1.6, sage); frame(0.3, 0.3, 7.12, 1.5, terra);
  // Relógio de parede minimalista (parede esquerda, x = 6,8)
  put(rot(cyl(0.15, 0.15, 0.02, black, 6.886, 1.95, 1.2, 28), 0, 0, Math.PI / 2));
  put(rot(cyl(0.138, 0.138, 0.012, paper, 6.902, 1.95, 1.2, 28), 0, 0, Math.PI / 2));
  put(box(0.01, 0.1, 0.006, black, 6.911, 2.0, 1.2, { cast: false }));
  put(rot(box(0.01, 0.07, 0.006, black, 6.911, 1.969, 1.229, { cast: false }), 1.0, 0, 0));
  // Geladeira no canto (sem divisória: cozinha aberta) + coluna de nogueira acima
  place(fridge(), 9.8, 0.45);
  put(box(0.78, 0.98, 0.7, walnut, 9.8, 2.3, 0.4));                                              // marcenaria sobre a geladeira (até o teto)
  put(box(0.7, 0.01, 0.01, led, 9.8, 1.808, 0.752, { cast: false }));
  // 22/11: removido a pedido do João (planta alta ao lado da geladeira)
  // Sofá baixo de linho virado para a TV
  place(sofa(), 7.68, 1.75, Math.PI);
  place(coffeeTable(), 7.68, 0.98);
  place(armchair(), 8.72, 1.3, -2.1);
  place(F.rug(1.9, 1.5, 0xd9cdb4), 7.68, 1.25);                                                  // tapete de lã creme
  // Sala de jantar: tapete claro, mesa oval, 4 cadeiras (lado do balcão livre para as banquetas), centro de mesa
  place(F.rug(1.7, 1.5, 0xd5c8ad), 9.2, 3.1);
  place(table(), 9.08, 3.12);
  place(tableTop(), 9.08, 3.12, 0, 0.778);
  for (const [cx, cz, ry] of [[8.1, 3.12, Math.PI / 2], [10.06, 3.12, -Math.PI / 2], [8.74, 3.84, Math.PI], [9.42, 3.84, Math.PI]]) {
    place(chair(), cx, cz, ry + (rnd() - 0.5) * 0.12);
  }
  // BALCÃO de cozinha (península baixa) EM FRENTE À GELADEIRA, a ~0,8 m dela: base de nogueira, tampo de pedra clara com
  // beiral para as banquetas (lado do jantar). Sem divisória em x=10,3: cozinha aberta, passagem livre dos dois lados.
  put(box(1.3, 0.86, 0.5, walnut, 9.8, 0.45, 1.9));
  put(box(1.3, 0.06, 0.44, black, 9.8, 0.03, 1.9, { cast: false }));
  put(box(1.5, 0.035, 0.66, marble, 9.8, 0.9, 1.96));
  put(box(1.24, 0.01, 0.01, led, 9.8, 0.1, 2.16, { cast: false }));
  for (const x of [9.45, 10.15]) { const st = stool(); st.scale.set(1, 1.12, 1); place(st, x, 2.45, rnd() * 0.5); }
  // Cortina no vidro da varanda (x 9,6–12,2): trilho preto, voil e painéis de linho nas laterais
  put(rot(cyl(0.01, 0.01, 2.8, black, 10.9, 2.4, 4.0, 8), 0, 0, Math.PI / 2));
  put(box(2.5, 2.3, 0.01, sheer, 10.9, 1.19, 4.075, { cast: false, receive: false }));
  for (const x0 of [9.66, 11.78]) {
    put(box(0.2, 2.34, 0.06, drape, x0 + 0.1, 1.21, 4.015, { cast: false }));
    put(box(0.18, 2.34, 0.09, drape, x0 + 0.3, 1.21, 4.015, { cast: false }));
  }

  // ======================= COZINHA (x 10,3–12,5) =======================
  // Fogão no canto esquerdo do fundo (fora da janela x 11–12), coifa embutida em coluna de nogueira até o teto
  place(stove(), 10.73, 0.39);
  put(cyl(0.1, 0.09, 0.1, inox, 10.59, 0.94, 0.25, 20));                                         // panela com tampa
  put(cyl(0.105, 0.105, 0.012, inox, 10.59, 0.996, 0.25, 20));
  put(sph(0.014, black, 10.59, 1.01, 0.25));
  put(cyl(0.11, 0.1, 0.035, black, 10.87, 0.91, 0.53, 20));                                      // frigideira
  put(box(0.025, 0.014, 0.18, black, 10.87, 0.92, 0.73));
  put(box(0.14, 0.2, 0.012, cream, 10.82, 0.45, 0.719, { cast: false }));                        // pano de prato
  put(box(0.64, 1.2, 0.5, walnut, 10.73, 2.2, 0.31));                                            // coluna da coifa (embutida)
  put(box(0.58, 0.02, 0.44, inox, 10.73, 1.59, 0.34));                                           // aba inox da coifa
  put(box(0.5, 0.01, 0.01, led, 10.73, 1.575, 0.58, { cast: false }));
  // Armários baixos de nogueira em L, tampo de pedra clara, rodapé preto recuado
  put(box(1.395, 0.8, 0.56, walnut, 11.7275, 0.46, 0.365));                                      // fundo (sob a janela)
  put(box(1.395, 0.06, 0.5, black, 11.7275, 0.03, 0.335, { cast: false }));
  put(box(1.395, 0.03, 0.62, marble, 11.7275, 0.875, 0.385));
  put(box(0.006, 0.7, 0.012, black, 11.725, 0.46, 0.65, { cast: false }));
  for (const x of [11.38, 12.07]) put(box(0.14, 0.012, 0.014, black, x, 0.83, 0.657));          // puxadores embutidos finos
  put(box(0.56, 0.8, 2.5, walnut, 12.145, 0.46, 1.95));                                          // parede direita (2,5 m)
  put(box(0.5, 0.06, 2.5, black, 12.175, 0.03, 1.95, { cast: false }));
  put(box(0.62, 0.03, 2.505, marble, 12.115, 0.875, 1.9475));
  for (let i = 1; i < 4; i++) put(box(0.012, 0.7, 0.006, black, 11.86, 0.46, 0.7 + i * 0.625, { cast: false }));
  for (let i = 0; i < 4; i++) put(box(0.014, 0.012, 0.14, black, 11.853, 0.83, 1.0125 + i * 0.625));
  // Painel de pedra clara atrás das bancadas (sem azulejo estampado) + fita LED sob os armários altos
  const bandX = (w, h, x, y, mat) => put(box(w, h, 0.012, mat, x, y, 0.081, { cast: false }));        // na parede do fundo (z = 0)
  const bandZ = (l, h, z, y, mat) => put(box(0.012, h, l, mat, 12.419, y, z, { cast: false }));      // na parede direita (x = 12,5)
  bandX(0.595, 0.58, 10.6725, 1.19, marble);                                                         // atrás do fogão
  bandX(0.395, 0.58, 12.2275, 1.19, marble);                                                         // à direita da janela
  bandZ(3.175, 0.58, 1.6625, 1.19, marble);
  put(box(0.01, 0.012, 2.4, led, 12.1, 1.435, 1.7, { cast: false }));                                // LED sob os armários
  // Armários superiores de nogueira até o teto (2,4 m), frentes lisas
  put(box(0.35, 1.3, 2.4, walnut, 12.25, 2.1, 1.7));
  for (const z of [1.1, 1.7, 2.3]) put(box(0.006, 1.25, 0.006, black, 12.072, 2.1, z, { cast: false }));
  for (const z of [0.8, 1.4, 2.0, 2.6]) put(box(0.014, 0.1, 0.012, black, 12.068, 1.6, z));
  // Pia inox embutida na pedra com misturador preto fosco
  put(box(0.46, 0.012, 0.52, inox, 12.13, 0.892, 1.65));
  put(box(0.4, 0.008, 0.46, stoneDk, 12.13, 0.9, 1.65, { cast: false }));
  put(cyl(0.011, 0.011, 0.26, black, 12.38, 1.02, 1.65, 8));
  put(box(0.17, 0.018, 0.018, black, 12.295, 1.15, 1.65));
  put(cyl(0.02, 0.024, 0.15, ceramic, 12.37, 0.97, 1.42, 12));
  put(box(0.06, 0.025, 0.04, sage, 12.36, 0.907, 1.88));
  // Escorredor discreto: 3 pratos em pé + 2 canecas
  put(box(0.36, 0.014, 0.4, inox, 12.14, 0.9, 2.25));
  for (let i = 0; i < 3; i++) put(rot(cyl(0.1, 0.1, 0.008, ceramic, 12.14, 1.01, 2.13 + i * 0.07, 20), Math.PI / 2));
  for (const x of [12.06, 12.2]) put(cyl(0.035, 0.03, 0.08, ceramic, x, 0.95, 2.4, 12));
  // Micro-ondas embutido preto (porta virada para a cozinha)
  put(box(0.35, 0.3, 0.5, black, 12.235, 1.05, 1.0));
  put(box(0.008, 0.24, 0.32, M.screenOff, 12.056, 1.05, 0.92, { cast: false }));
  put(box(0.008, 0.24, 0.1, inox, 12.056, 1.05, 1.15, { cast: false }));
  // Cafeteira e liquidificador pretos na bancada do fundo
  put(box(0.14, 0.3, 0.09, black, 11.25, 1.04, 0.445));
  put(box(0.14, 0.11, 0.22, black, 11.25, 1.135, 0.5));
  put(cyl(0.05, 0.045, 0.14, glassy, 11.25, 0.965, 0.55, 14));
  put(box(0.13, 0.13, 0.13, black, 11.65, 0.955, 0.5));
  put(cyl(0.06, 0.045, 0.2, glassy, 11.65, 1.12, 0.5, 12));
  put(cyl(0.062, 0.062, 0.02, black, 11.65, 1.23, 0.5, 12));
  // Cesto de vime com frutas no canto da bancada
  put(cyl(0.14, 0.11, 0.09, wicker, 12.16, 0.935, 0.4, 16));
  put(sph(0.04, fruit[1], 12.12, 0.99, 0.37)); put(sph(0.04, fruit[0], 12.2, 0.99, 0.43)); put(sph(0.038, fruit[3], 12.15, 1.025, 0.44));
  // 22/11: removido a pedido do João (temperos em vasinhos na janela)
  // Tábua de corte, rolo de papel-toalha, lixeira inox, tapete de cozinha
  put(box(0.3, 0.015, 0.2, oak, 12.16, 0.8975, 2.85));
  put(cyl(0.055, 0.055, 0.24, paper, 12.3, 1.01, 3.1, 14));
  put(cyl(0.13, 0.12, 0.5, inox, 12.15, 0.25, 3.55, 20));
  put(cyl(0.135, 0.135, 0.03, black, 12.15, 0.515, 3.55, 20));
  // Mesa de cozinha de madeira (0,8 x 0,8) no espaço livre do meio, 3 cadeiras, tapete; folga dos armários e do balcão
  place(F.rug(1.3, 1.5, 0xb7b896), 11.1, 2.7);
  put(box(0.84, 0.035, 0.84, oak, 11.1, 0.76, 2.7));
  for (const [sx, sz] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) put(box(0.05, 0.74, 0.05, black, 11.1 + sx * 0.37, 0.37, 2.7 + sz * 0.37));
  put(box(0.5, 0.012, 0.18, cream, 11.1, 0.784, 2.7)); put(cyl(0.09, 0.07, 0.04, ceramic, 11.1, 0.805, 2.7, 20));
  for (const [cx, cz, ry] of [[11.1, 2.17, 0], [11.1, 3.23, Math.PI], [10.5, 2.7, Math.PI / 2]]) place(chair(), cx, cz, ry);
  // 22/11: removido a pedido do João (prateleira na antiga meia-parede x=10,3 — divisória não existe)
}
