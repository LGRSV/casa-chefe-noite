function roomGaragemJardim(ctx) {
  const { THREE, M, box, cyl, sph, place, add, std, rnd } = ctx;
  const G = () => new THREE.Group();
  const V = (x, y, z) => new THREE.Vector3(x, y, z);
  const j = (k) => (rnd() - 0.5) * 2 * k;                      // jitter determinístico ±k
  const flat = (m) => { m.castShadow = false; return m; };     // peças rasteiras não projetam sombra

  // Paleta local (estilo do vídeo): concreto claro, carvalho, preto fosco, verde-sálvia, terracota em detalhe, folhagem viva
  const P = {
    stone: std({ color: 0xbdb7aa, roughness: 0.95 }), stone2: std({ color: 0xd2ccbe, roughness: 0.95 }), stoneDk: std({ color: 0xa39d90, roughness: 0.95 }),
    gravel: std({ color: 0xded8c9, roughness: 1 }), iron: std({ color: 0x232426, roughness: 0.85, metalness: 0.15 }), ironLt: std({ color: 0x3a3b3e, roughness: 0.8, metalness: 0.15 }),
    rubber: std({ color: 0x34353a, roughness: 1 }), yellow: std({ color: 0xece4d0, roughness: 0.9 }), paintWhite: std({ color: 0xeeeae0, roughness: 0.9 }),
    peg: std({ color: 0xcdb48a, roughness: 0.85 }), cardboard: std({ color: 0xd6cbb2, roughness: 1 }), crate: std({ color: 0x7c8a6a, roughness: 0.85 }),
    binGreen: std({ color: 0x7e8c70, roughness: 0.85 }), binGreenDk: std({ color: 0x5f6b54, roughness: 0.85 }), binBlue: std({ color: 0x26272a, roughness: 0.85 }), binBlueDk: std({ color: 0x18191b, roughness: 0.85 }),
    bike: std({ color: 0x74836a, roughness: 0.5, metalness: 0.2 }), hose: std({ color: 0x6f7f5f, roughness: 0.8 }), drill: std({ color: 0x2b2c2e, roughness: 0.7 }),
    redTool: std({ color: 0xb2623f, roughness: 0.7 }), ceramic: std({ color: 0xe2d8c6, roughness: 0.85 }), plastic: std({ color: 0x8a8f8c, roughness: 0.7 }),
    leafDk: std({ color: 0x2f7436, roughness: 1 }), leafLt: std({ color: 0x7fc043, roughness: 1 }), palm: std({ color: 0x4fa83e, roughness: 0.9 }), silver: std({ color: 0x8fb28a, roughness: 1 }),
    pink: std({ color: 0xe0907a, roughness: 0.9 }), lilac: std({ color: 0xb9a4d6, roughness: 0.9 }), cream: std({ color: 0xf3ecdb, roughness: 0.9 }), lampGlass: std({ color: 0xffeccb, emissive: 0xffc98a, emissiveIntensity: 0.9, roughness: 0.5 }),
    oak: std({ color: 0xc9a672, roughness: 0.7 }), walnut: std({ color: 0x5a3d2b, roughness: 0.65 }), black: std({ color: 0x1f2022, roughness: 0.8 }),
    terra: std({ color: 0xb8643f, roughness: 0.9 }), linen: std({ color: 0xe4dac4, roughness: 0.95 }), led: std({ color: 0xfff0d0, emissive: 0xffc27a, emissiveIntensity: 1.4 }),
  };

  // ---- builders locais ------------------------------------------------------------------------
  // cilindro entre dois pontos (tubos de bicicleta, galhos, mangueira)
  const tube = (g, a, b, r, mat, seg = 8) => {
    const A = V(...a), B = V(...b), d = B.clone().sub(A);
    const m = cyl(r, r, d.length(), mat, 0, 0, 0, seg);
    m.position.copy(A).add(B).multiplyScalar(0.5);
    m.quaternion.setFromUnitVectors(V(0, 1, 0), d.normalize());
    g.add(m); return m;
  };
  // toro (rodas, anéis de mangueira, cabeça de chave)
  const torus = (r, t, mat, x, y, z, rx = 0, ry = 0, seg = 20) => {
    const m = new THREE.Mesh(new THREE.TorusGeometry(r, t, 8, seg), mat);
    m.position.set(x, y, z); m.rotation.set(rx, ry, 0); m.castShadow = true; m.receiveShadow = true; return m;
  };
  // folha comprida saindo de (cx,cy,cz): ângulo `a` no plano, inclinação `t` (positivo = caindo)
  const frond = (g, cx, cy, cz, len, w, a, t, mat) => {
    const m = box(len, 0.02, w, mat, 0, 0, 0), L = len / 2, ct = Math.cos(t);
    m.position.set(cx + L * ct * Math.cos(a), cy - L * Math.sin(t), cz - L * ct * Math.sin(a));
    m.rotation.set(0, a, -t);
    g.add(m); return m;
  };
  const loose = G();                                          // tubos soltos no nível da cena

  // =============================== GARAGEM (x 0–3 · z 10,6–16) ===============================
  // Vaga: tapete de borracha + faixas amarelas (o up! do cartão fica em cima, centrado em (1,5, 13,6))
  const slab = std({ color: 0xd8d4ca, roughness: 0.95 });
  add(box(2.9, 0.01, 5.3, slab, 1.5, 0.012, 13.3, { cast: false }));
  for (const z of [11.9, 13.3, 14.7]) add(box(2.9, 0.012, 0.012, P.stoneDk, 1.5, 0.014, z, { cast: false }));   // juntas de dilatação
  add(box(1.8, 0.012, 3.8, P.rubber, 1.5, 0.02, 13.6, { cast: false }));
  for (const x of [0.52, 2.48]) add(box(0.08, 0.008, 4.0, P.yellow, x, 0.02, 13.6, { cast: false }));
  add(box(2.04, 0.008, 0.08, P.yellow, 1.5, 0.02, 11.62, { cast: false }));

  // Armário de ferramentas (aço, tampo de madeira, 2 portas + 2 gavetas, maleta e lata em cima)
  const toolCabinet = () => {
    const g = G();
    g.add(box(0.86, 0.05, 0.36, M.dark, 0, 0.025, 0));                       // rodapé
    g.add(box(0.9, 0.85, 0.4, P.black, 0, 0.475, 0));                        // corpo (y 0,05–0,90)
    g.add(box(0.96, 0.05, 0.46, P.oak, 0, 0.925, 0));                       // tampo
    g.add(box(0.01, 0.55, 0.01, P.ironLt, 0, 0.34, 0.2));                      // frincha entre as portas
    for (const sx of [-1, 1]) {
      g.add(box(0.012, 0.3, 0.014, M.chrome, sx * 0.04, 0.4, 0.212));    // puxadores das portas
      g.add(box(0.42, 0.22, 0.012, P.walnut, sx * 0.22, 0.76, 0.206));       // frentes das gavetas
      g.add(box(0.26, 0.012, 0.014, M.chrome, sx * 0.22, 0.8, 0.216));        // puxadores das gavetas
    }
    g.add(box(0.4, 0.16, 0.2, P.terra, -0.2, 1.03, 0));                    // maleta de ferramentas
    g.add(box(0.16, 0.02, 0.025, M.dark, -0.2, 1.12, 0));                    // alça
    g.add(cyl(0.075, 0.075, 0.16, P.cream, 0.25, 1.03, -0.06, 14));           // lata de tinta
    return g;
  };
  place(toolCabinet(), 0.55, 10.95);

  // Painel de ferramentas (pegboard) na parede do fundo (z=10,6), acima do armário
  add(box(1.5, 0.75, 0.02, P.peg, 0.9, 1.55, 10.686));
  const zt = 10.712;                                                         // plano das ferramentas
  add(box(0.03, 0.3, 0.025, M.wood, 0.35, 1.45, zt)); add(box(0.12, 0.05, 0.04, M.dark, 0.35, 1.62, zt));           // martelo
  add(box(0.03, 0.26, 0.02, M.chrome, 0.62, 1.5, zt)); add(torus(0.035, 0.012, M.chrome, 0.62, 1.66, zt));            // chave fixa
  add(box(0.2, 0.08, 0.06, P.drill, 1.35, 1.64, zt + 0.02)); add(box(0.05, 0.14, 0.05, M.dark, 1.31, 1.52, zt + 0.02)); // furadeira
  const chuck = cyl(0.02, 0.02, 0.06, M.chrome, 1.48, 1.64, zt + 0.02, 8); chuck.rotation.z = Math.PI / 2; add(chuck);   // mandril
  add(box(0.34, 0.09, 0.006, M.steel, 1.0, 1.3, zt)); add(box(0.1, 0.1, 0.02, M.wood, 1.22, 1.3, zt));             // serrote
  add(box(0.4, 0.04, 0.025, P.yellow, 0.5, 1.28, zt));                                                             // nível

  // Prateleira alta com caixas (parede do fundo, y 2,2)
  add(box(2.7, 0.03, 0.35, P.oak, 1.45, 2.2, 10.86));
  add(box(2.6, 0.012, 0.02, P.led, 1.45, 2.18, 10.95, { cast: false }));          // fita LED sob a prateleira
  for (const x of [0.4, 2.5]) add(box(0.03, 0.26, 0.3, P.black, x, 2.06, 10.85));
  add(box(0.5, 0.36, 0.32, P.cardboard, 0.45, 2.395, 10.86));
  add(box(0.4, 0.28, 0.3, P.cardboard, 1.05, 2.355, 10.86));
  add(box(0.45, 0.3, 0.32, P.crate, 1.6, 2.365, 10.86));
  add(box(0.34, 0.24, 0.28, P.cardboard, 2.25, 2.335, 10.86));

  // Bicicleta encostada na parede x=0 (frente em -z; rodas = toros, quadro = tubos)
  const bicycle = () => {
    const g = G(), R = [0, 0.355, 0.52], F = [0, 0.355, -0.52], BB = [0, 0.3, 0.08], S = [0, 0.86, 0.25], Hb = [0, 0.7, -0.4], H = [0, 0.86, -0.35];
    for (const w of [R, F]) g.add(torus(0.33, 0.025, M.tire, w[0], w[1], w[2], 0, Math.PI / 2, 24));
    for (const [a, b] of [[BB, S], [BB, Hb], [S, H], [BB, R], [S, R], [Hb, F], [Hb, H]]) tube(g, a, b, 0.016, P.bike);
    tube(g, S, [0, 0.98, 0.28], 0.012, M.chrome);                             // canote
    g.add(box(0.12, 0.05, 0.26, M.dark, 0, 1.0, 0.3));                       // selim
    const bar = cyl(0.012, 0.012, 0.48, M.dark, 0, 0.95, -0.4, 8); bar.rotation.z = Math.PI / 2; g.add(bar);   // guidão
    return g;
  };
  const bike = place(bicycle(), 0.42, 12.7); bike.rotation.z = 0.07;         // leve inclinação contra a parede

  // Mangueira enrolada pendurada num gancho (parede x=0, perto do portão)
  add(box(0.08, 0.03, 0.1, P.ironLt, 0.115, 1.0, 15.2));
  add(torus(0.2, 0.03, P.hose, 0.17, 0.8, 15.2, 0, Math.PI / 2, 24));
  add(cyl(0.015, 0.015, 0.14, P.hose, 0.2, 0.52, 15.1, 8));

  // Lixeiras no canto do fundo, balde, quadro de luz junto ao portão
  add(cyl(0.2, 0.18, 0.62, P.binGreen, 2.62, 0.31, 10.95, 14)); add(cyl(0.22, 0.2, 0.05, P.binGreenDk, 2.62, 0.645, 10.95, 14));
  add(cyl(0.18, 0.16, 0.55, P.binBlue, 2.18, 0.275, 10.95, 14)); add(cyl(0.2, 0.18, 0.05, P.binBlueDk, 2.18, 0.575, 10.95, 14));
  add(cyl(0.14, 0.12, 0.28, P.plastic, 1.4, 0.14, 10.92, 12));
  add(box(0.06, 0.32, 0.24, P.paintWhite, 0.105, 1.6, 15.55));

  // ============================ JARDIM (grama x 10,9–13,4 · z 6,2–12,4) ============================
  // Canteiro ao longo do muro (x=13,4): terra + borda de pedra em segmentos irregulares
  add(box(0.7, 0.05, 5.3, M.soil, 12.94, 0.03, 9.07, { cast: false }));
  for (let i = 0; i < 4; i++) {
    const h = 0.1 + rnd() * 0.05, s = box(0.14, h, 1.31, i % 2 ? P.stone2 : P.stone, 12.55 + j(0.01), h / 2, 7.07 + i * 1.335);
    s.rotation.y = j(0.03); add(s);
  }
  for (const z of [6.4, 11.75]) add(box(0.77, 0.12, 0.14, P.stone, 12.935, 0.06, z));
  // Pedriscos: faixa entre o caminho e o canteiro + roda em volta da árvore
  add(box(0.25, 0.012, 5.1, P.gravel, 12.375, 0.018, 9.05, { cast: false }));
  // 22/11: roda de pedriscos da árvore removida junto com ela

  // Árvore (tronco afunilado, 3 galhos, copa em três verdes; copa puxada para o lado do deck, longe da arandela)
  const tree = () => {
    const g = G();
    g.add(cyl(0.1, 0.15, 2.1, M.trunk, 0, 1.05, 0, 10));
    tube(g, [0, 1.85, 0], [-0.5, 2.5, 0.25], 0.05, M.trunk); tube(g, [0, 1.95, 0], [0.3, 2.55, -0.35], 0.045, M.trunk); tube(g, [0, 2.05, 0], [-0.15, 2.75, -0.4], 0.04, M.trunk);
    const balls = [[-0.45, 2.6, 0.25, 0.6], [0.3, 2.65, -0.35, 0.55], [-0.15, 2.95, -0.35, 0.55], [0.35, 2.45, 0.3, 0.5], [-0.6, 2.3, -0.15, 0.48], [0.05, 3.2, 0.05, 0.5]];
    balls.forEach(([x, y, z, r], i) => g.add(sph(r + j(0.03), [M.plant, M.leaf2, P.leafDk][i % 3], x + j(0.05), y, z + j(0.05))));
    return g;
  };
  // 22/11: removida a pedido do João -> place(tree(), 12.3, 11.9);

  // Palmeiras pequenas: tronco em anéis + folhas caídas em leque (abrem para o lado do jardim, não para o muro)
  const palm = (h, n, len, w, segs) => {
    const g = G(); const sh = h / segs;
    for (let i = 0; i < segs; i++) g.add(cyl(0.06 - i * 0.008, 0.075 - i * 0.008, sh, i % 2 ? M.trunk : M.woodDark, 0, sh * (i + 0.5), 0, 8));
    for (let i = 0; i < n; i++) { const a = Math.PI + (i - (n - 1) / 2) * (3.6 / (n - 1)); frond(g, 0, h, 0, len, w, a + j(0.08), 0.35 + rnd() * 0.4, i % 2 ? P.palm : M.leaf2); }
    g.add(sph(0.07, P.leafLt, 0, h + 0.03, 0));
    return g;
  };
  // 22/11: removida a pedido do João -> place(palm(1.45, 6, 1.0, 0.18, 2), 12.95, 7.3);
  // 22/11: removida a pedido do João -> place(palm(0.95, 5, 0.75, 0.15, 1), 12.95, 10.0);

  // Arbustos (3 esferas em verdes diferentes) e touceiras com flores discretas
  const shrub = (x, z, s, m1, m2) => {
    add(sph(0.32 * s, m1, x, 0.28 * s, z)); add(sph(0.25 * s, m2, x - 0.18 * s, 0.26 * s, z + 0.15 * s)); add(sph(0.22 * s, P.leafLt, x + 0.13 * s, 0.32 * s, z - 0.17 * s));
  };
  shrub(12.9, 6.78, 1.0, P.leafDk, M.leaf2); shrub(12.95, 8.9, 0.85, M.plant, P.silver); shrub(12.9, 11.25, 0.95, P.leafDk, M.plant);
  const flowers = (x, z, bloom, r = 0.05, tall = 1) => {
    add(sph(0.2, M.leaf2, x, 0.16, z));
    for (let i = 0; i < 2; i++) { const a = rnd() * Math.PI * 2, d = 0.06 + rnd() * 0.1; const b = sph(r, bloom, x + Math.cos(a) * d, 0.3 + rnd() * 0.05, z + Math.sin(a) * d); b.scale.y = tall; add(b); }
  };
  flowers(13.0, 7.95, P.pink); flowers(12.95, 8.45, P.cream, 0.04); flowers(12.95, 10.65, P.lilac, 0.035, 2.4);

  // Jardineira longa de carvalho com folhagem junto ao vidro da varanda + vasos grandes (creme e terracota)
  add(box(1.3, 0.42, 0.4, P.oak, 11.3, 0.21, 6.7)); add(box(1.2, 0.02, 0.3, M.soil, 11.3, 0.43, 6.7, { cast: false }));
  for (let i = 0; i < 5; i++) { const b = sph(0.17 + rnd() * 0.05, [P.leafDk, P.palm, P.leafLt][i % 3], 10.85 + i * 0.23, 0.58 + rnd() * 0.08, 6.7); b.scale.y = 1.15; add(b); }
  const bigPot = (x, z, mat, h, plant) => {
    add(cyl(0.3, 0.24, h, mat, x, h / 2, z, 20)); add(cyl(0.27, 0.27, 0.02, M.soil, x, h, z, 16));
    const gp = G(); for (let i = 0; i < 6; i++) frond(gp, 0, h, 0, 0.7, 0.1, i * 1.047 + j(0.15), -1.1 + rnd() * 0.3, i % 2 ? P.leafLt : plant); place(gp, x, z);
    add(sph(0.2, plant, x, h + 0.25, z));
  };
  bigPot(11.25, 8.4, P.ceramic, 0.62, P.palm); bigPot(11.2, 10.9, P.terra, 0.55, P.leafDk);

  // Caminho de lajotas: pátio → jardim → varanda (desvia do tronco), e da varanda ao deck (porta e vidro)
  const stone = (x, z, i) => { const s = box(0.42, 0.03, 0.34, [P.stone, P.stone2, P.stoneDk][i % 3], x + j(0.04), 0.03, z, { cast: false }); s.rotation.y = j(0.12); add(s); };
  for (let i = 0; i < 9; i++) { const z = 6.55 + i * 0.72; stone(12.0 - 0.12 * Math.min(1, Math.max(0, (z - 10.8) / 1.2)), z, i); }
  [[3.35, 6.5], [3.35, 6.9], [10.0, 6.5], [10.0, 6.9]].forEach(([x, z], i) => stone(x, z, i));

  // Balizadores minimalistas (coluna preta fosca com fenda de luz âmbar)
  for (const z of [7.0, 9.2, 11.25]) {
    add(box(0.07, 0.5, 0.07, P.black, 12.34, 0.25, z)); add(box(0.075, 0.1, 0.012, P.led, 12.34, 0.42, z + 0.04, { cast: false })); add(box(0.08, 0.02, 0.08, P.ironLt, 12.34, 0.51, z));
  }

  // Torneira de jardim no muro (perto da bomba) + mangueira enrolada na grama
  add(cyl(0.012, 0.012, 0.62, M.chrome, 13.3, 0.31, 12.2, 8));
  const tapBody = cyl(0.02, 0.02, 0.1, M.chrome, 13.25, 0.62, 12.2, 8); tapBody.rotation.z = Math.PI / 2; add(tapBody);
  add(box(0.05, 0.012, 0.012, P.redTool, 13.2, 0.66, 12.2)); add(cyl(0.01, 0.01, 0.08, M.chrome, 13.2, 0.57, 12.2, 8));
  add(torus(0.22, 0.022, P.hose, 12.85, 0.03, 12.15, Math.PI / 2, 0, 24));
  tube(loose, [13.2, 0.53, 12.2], [12.98, 0.05, 12.34], 0.013, P.hose);

  // ======================= PÁTIO / ENTRADA (asfalto x 2,4–13,4 · z 12,4–16,6) =======================
  // Vaga de visitante pintada no asfalto, em frente ao vão da garagem (x 3,4–8,0 · z 12,95–15,35) + calço de roda
  for (const z of [12.95, 15.35]) add(box(4.6, 0.006, 0.1, P.paintWhite, 5.7, 0.018, z, { cast: false }));
  add(box(0.1, 0.006, 2.5, P.paintWhite, 8.0, 0.018, 14.15, { cast: false }));
  add(box(0.15, 0.1, 0.55, P.yellow, 7.6, 0.05, 14.15));

  // Caixa de correio na face interna do muro, ao lado do portão de pedestre (x 5,6–6,6)
  add(box(0.3, 0.22, 0.14, M.white, 5.25, 1.35, 15.855)); add(box(0.22, 0.02, 0.012, M.dark, 5.25, 1.42, 15.78)); add(box(0.02, 0.1, 0.04, P.redTool, 5.42, 1.42, 15.84));

  // Lixeira com rodas, banco de pedra e vaso grande com buxinho junto ao portão
  add(box(0.5, 0.85, 0.55, P.binGreen, 4.6, 0.5, 15.6)); add(box(0.54, 0.06, 0.59, P.binGreenDk, 4.6, 0.955, 15.6));
  for (const sx of [-1, 1]) { const w = cyl(0.09, 0.09, 0.05, M.dark, 4.6 + sx * 0.27, 0.09, 15.82, 12); w.rotation.z = Math.PI / 2; add(w); }
  add(box(1.4, 0.07, 0.42, P.oak, 9.6, 0.445, 15.65)); for (const sx of [-1, 1]) add(box(0.14, 0.41, 0.36, P.stone, 9.6 + sx * 0.55, 0.205, 15.65));
  add(cyl(0.3, 0.26, 0.65, P.ceramic, 7.1, 0.325, 15.6, 20)); add(cyl(0.27, 0.27, 0.02, M.soil, 7.1, 0.65, 15.6, 16));
  add(sph(0.36, P.leafDk, 7.1, 1.0, 15.6)); add(sph(0.22, P.leafLt, 7.25, 1.17, 15.5));
  add(box(1.5, 0.34, 0.34, P.oak, 11.6, 0.17, 15.65)); add(box(1.4, 0.02, 0.26, M.soil, 11.6, 0.35, 15.65, { cast: false }));   // jardineira de carvalho junto ao muro
  for (let i = 0; i < 4; i++) add(sph(0.16 + rnd() * 0.04, [P.leafDk, P.palm, P.leafLt, P.silver][i], 11.15 + i * 0.32, 0.5, 15.65));

  // Tampa de bueiro redonda no meio do pátio e grelha de escoamento junto ao muro
  add(flat(cyl(0.3, 0.3, 0.02, P.iron, 10.3, 0.022, 14.6, 20))); add(flat(cyl(0.24, 0.24, 0.008, P.ironLt, 10.3, 0.036, 14.6, 20)));
  add(box(0.4, 0.02, 0.3, P.iron, 4.0, 0.02, 15.35, { cast: false })); for (let i = 0; i < 3; i++) add(box(0.03, 0.012, 0.28, P.ironLt, 3.9 + i * 0.1, 0.034, 15.35, { cast: false }));

  place(loose, 0, 0);
}
