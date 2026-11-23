function roomVarandaPiscina(ctx) {
  // 22/11 (João): o corredor/varanda NÃO existe. Faixa x 0-12,5 · z 4,2-6,2 = ÁREA EXTERNA ABERTA (piso do deck, sem parede em z=6,2, sem forro).
  //   Portas z=4,2 dos quartos/sala fechadas; só janelas (x 2,5-3,3 e 5,5-6,4) e o vidro da cozinha (x 9,6-12,2). Texto abaixo é histórico.
  // VARANDA coberta — x 0–12,5 · z 4,2–6,2 (faces internas: x 0,075/12,425 · z 4,275/6,125).
  //   Parede da casa (z=4,2): porta casal x 1,0–1,9 · janela x 2,5–3,3 · porta quarto x 4,1–5,0 · janela x 5,5–6,4 ·
  //   porta sala x 7,4–8,3 · vidro do balcão x 9,6–12,2. Parede externa (z=6,2): porta p/ deck x 2,9–3,8 ·
  //   janela x 4,6–6,6 · vidro x 8,0–12,0. Pendentes em (2,1/6,3/10,4 · 2,5 · 5,2) — objetos do cartão.
  // DECK — x 2,9–10,9 · z 7,2–12,4; borda de pedra da piscina x 3,6–10,2 · z 7,9–11,7 (meia-lua centro 8,3/9,8 r 1,9).
  // Faixas de grama: z 6,2–7,2 (entre varanda e deck) e x 2,4–2,9 (à esquerda do deck).
  // Layout: toda a mobília da varanda encostada na parede da casa, corredor livre ≥ 1 m ao longo de z ≈ 5,2
  //   (de x 0 até 10,7); rede no canto esquerdo (junto à parede externa cega x 0–2,9); sofá centrado na janela
  //   x 4,6–6,6; churrasqueira + cervejeira entre a porta da sala e o vidro do balcão; mesa de madeira com bancos
  //   no fundo direito (x > 10,7, sem passagem necessária). Deck: escadas nas posições originais, espreguiçadeiras na
  //   faixa sul, cadeiras de piscina no canto SE (mesa redonda e guarda-sol removidos em 22/11), ducha e
  //   tochas na faixa oeste, boias na água.
  const { THREE, M, box, cyl, sph, place, add, std, rnd } = ctx;
  const G = () => new THREE.Group();
  const put = (m, x, y, z, rx = 0, ry = 0, rz = 0) => { m.position.set(x, y, z); m.rotation.set(rx, ry, rz); return m; };
  // cilindro entre dois pontos (a → b), raio ra em a e rb em b
  const rod = (mat, ra, rb, ax, ay, az, bx, by, bz, seg = 8) => {
    const dir = new THREE.Vector3(bx - ax, by - ay, bz - az), len = dir.length();
    const m = cyl(rb, ra, len, mat, (ax + bx) / 2, (ay + by) / 2, (az + bz) / 2, seg);
    m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.normalize());
    return m;
  };
  // cone/folha inclinado: base em (x,y,z), inclinação `tilt` da vertical, apontando para o azimute `a`
  const leaf = (mat, r, len, x, y, z, tilt, a, flat = 0.3, seg = 5) => {
    const m = cyl(0, r, len, mat, 0, 0, 0, seg);
    m.scale.z = flat; m.rotation.order = 'YXZ'; m.rotation.set(tilt, a, 0);
    m.position.set(x + Math.sin(a) * Math.sin(tilt) * len / 2, y + Math.cos(tilt) * len / 2, z + Math.cos(a) * Math.sin(tilt) * len / 2);
    return m;
  };

  // ---------------- paleta (estilo do video): linho, carvalho, salvia, pedra clara, preto fosco, terracota em detalhe ----------------
  const navy    = std({ color: 0x86967a, roughness: 0.9 });          // verde-salvia (almofadas, boias, toalhas)
  const fibra   = std({ color: 0xd9cfba, roughness: 0.95 });         // linho creme (estofados)
  const linen   = std({ color: 0xf4efe4, roughness: 0.95 });         // tecido/almofadas
  const teak    = std({ color: 0xc8a26c, roughness: 0.7 });          // carvalho claro
  const bamboo  = std({ color: 0xb99a66, roughness: 0.8 });
  const plaster = std({ color: 0xf1ece2, roughness: 0.95 });         // alvenaria rebocada
  const brick   = std({ color: 0xa8613f, roughness: 0.95 });         // terracota
  const granite = std({ color: 0x242527, roughness: 0.4, metalness: 0.1 });   // pedra escura / preto fosco
  const ceramic = std({ color: 0xe9e2d3, roughness: 0.55 });         // vasos creme
  const stone   = std({ color: 0xded7c6, roughness: 0.95 });         // pedra clara
  const coir    = std({ color: 0xbfae8a, roughness: 1 });            // capacho
  const agave   = std({ color: 0x7fa377, roughness: 0.9 });
  const green   = std({ color: 0x3a7a46, roughness: 0.3 });          // garrafas
  const amber   = std({ color: 0x8a4b12, roughness: 0.3 });
  const lime    = std({ color: 0xc9e36b, roughness: 0.2, transparent: true, opacity: 0.75 });
  const ember   = std({ color: 0xff6a1a, emissive: 0xff4500, emissiveIntensity: 1.3 });
  const flame   = std({ color: 0xffb347, emissive: 0xff8a1a, emissiveIntensity: 1.8 });
  const lampOn  = std({ color: 0xfff3d6, emissive: 0xffd08a, emissiveIntensity: 1.0 });
  const ledCool = std({ color: 0xfff0d0, emissive: 0xffc88a, emissiveIntensity: 1.2 });
  const blk     = std({ color: 0x17181a, roughness: 0.6, metalness: 0.2 });   // preto fosco (pes e mastros finos)
  const aqua    = std({ color: 0xbff7f2, emissive: 0x3fe3d8, emissiveIntensity: 2.2 });   // luz subaquatica
  const canopy  = new THREE.MeshStandardMaterial({ color: 0xe8dcc3, roughness: 0.9, side: THREE.DoubleSide });
  const canopyW = new THREE.MeshStandardMaterial({ color: 0xf7f3ea, roughness: 0.9, side: THREE.DoubleSide });

  // =====================================================================================
  // VARANDA
  // =====================================================================================

  // 22/11: removido a pedido do João (palmeira em vaso do canto esquerdo)

  // ---- rede (hammock) armada entre gancho na parede x=0 e coluna de madeira, ao longo da parede externa ----
  {
    const zc = 5.72, x0 = 0.62, x1 = 2.2, yEnd = 1.42, sag = 0.62;
    // corpo: malha listrada marinho/branco (cores por vértice), catenária com bordas erguidas
    const NU = 18, stripes = 7, pos = [], col = [], uv = [], idx = [];
    const cNavy = new THREE.Color(0x8c9b7d), cWhite = new THREE.Color(0xefe8d8);
    let vi = 0;
    for (let j = 0; j < stripes; j++) {
      const c = j % 2 ? cWhite : cNavy;
      for (const v of [-1 + (2 * j) / stripes, -1 + (2 * (j + 1)) / stripes]) {
        for (let i = 0; i <= NU; i++) {
          const u = i / NU, s = Math.sin(Math.PI * u), hw = 0.06 + 0.26 * s;
          pos.push(x0 + u * (x1 - x0), yEnd - sag * s + 0.16 * v * v * s, zc + v * hw);
          col.push(c.r, c.g, c.b); uv.push(u, (v + 1) / 2);
        }
      }
      const a = vi, b = vi + NU + 1;
      for (let i = 0; i < NU; i++) idx.push(a + i, b + i, a + i + 1, b + i, b + i + 1, a + i + 1);
      vi += 2 * (NU + 1);
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    geo.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
    geo.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
    geo.setIndex(idx); geo.computeVertexNormals();
    const body = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.95, side: THREE.DoubleSide }));
    body.castShadow = true; body.receiveShadow = true; body.userData.keep = true; add(body);
    // punhos (leque de cordas) até os ganchos
    add(rod(linen, 0.05, 0.012, x0, yEnd, zc, 0.1, 1.9, zc));
    add(rod(linen, 0.05, 0.012, x1, yEnd, zc, 2.64, 1.9, zc));
    add(box(0.02, 0.1, 0.1, M.chrome, 0.085, 1.9, zc));                    // chapa do gancho na parede x=0
    add(box(0.1, 2.8, 0.1, blk, 2.72, 1.4, zc));                   // coluna de madeira da cobertura
    add(sph(0.022, M.chrome, 2.64, 1.9, zc));                              // gancho na coluna
    add(box(0.42, 0.1, 0.26, navy, (x0 + x1) / 2, yEnd - sag + 0.06, zc)); // almofada
  }

  // ---- capacho na porta para o deck (x 2,9–3,8) + vaso entre a janela e a porta do quarto ----
  // 22/11: removido a pedido do João (capacho da porta para o deck: a porta e a parede z=6,2 não existem)
  // 22/11: removido a pedido do João (vaso junto à porta do quarto)

  // ---- sofá de fibra marinho com almofadas de linho, centrado na janela da varanda (x 4,6–6,6) ----
  {
    const g = G(), w = 1.9, d = 0.75;
    g.add(box(w - 0.3, 0.06, d - 0.3, blk, 0, 0.03, 0));                // base recuada (sombra)
    g.add(box(w, 0.3, d, fibra, 0, 0.23, 0));
    g.add(box(0.14, 0.55, d, fibra, -w / 2 + 0.07, 0.355, 0)); g.add(box(0.14, 0.55, d, fibra, w / 2 - 0.07, 0.355, 0));
    g.add(box(w - 0.28, 0.45, 0.14, fibra, 0, 0.605, -d / 2 + 0.07));
    const cw = (w - 0.28) / 3;
    for (let i = 0; i < 3; i++) {
      const cx = -w / 2 + 0.14 + cw * (i + 0.5);
      g.add(box(cw - 0.04, 0.12, d - 0.3, linen, cx, 0.44, 0.06));
      g.add(put(box(cw - 0.06, 0.34, 0.1, linen, 0, 0, 0), cx, 0.65, -d / 2 + 0.2, -0.14));
    }
    g.add(put(box(0.38, 0.38, 0.1, navy, 0, 0, 0), -w / 2 + 0.4, 0.68, -d / 2 + 0.28, -0.2, 0, 0.35));
    g.add(put(box(0.38, 0.38, 0.1, brick, 0, 0, 0), w / 2 - 0.4, 0.68, -d / 2 + 0.28, -0.2, 0, -0.3));
    place(g, 6.3, 4.73);   // z 4,355–5,105 → corredor 5,105–6,125 (1,02 m)
  }

  // ---- churrasqueira de alvenaria com coifa e chaminé (x 8,42–9,58, entre a porta da sala e o vidro do balcão) ----
  {
    const g = G(), w = 1.16, d = 0.62;
    g.add(box(w, 0.86, d - 0.02, plaster, 0, 0.43, -0.01));                      // corpo rebocado
    g.add(box(0.5, 0.42, 0.03, M.dark, -0.27, 0.3, d / 2 - 0.015));                // nicho da lenha
    for (const [lx, ly] of [[-0.36, 0.15], [-0.18, 0.15]]) g.add(put(cyl(0.06, 0.06, 0.5, M.trunk, 0, 0, 0, 8), lx, ly, d / 2 - 0.2, Math.PI / 2));
    g.add(box(0.46, 0.6, 0.03, M.woodDark, 0.3, 0.4, d / 2 - 0.005));              // porta do armário
    g.add(cyl(0.01, 0.01, 0.12, M.chrome, 0.48, 0.42, d / 2 + 0.015, 6));          // puxador
    g.add(box(w + 0.02, 0.05, d + 0.04, granite, 0, 0.885, 0));                     // bancada de granito
    g.add(box(w - 0.3, 0.05, d - 0.16, ember, 0, 0.935, 0.02));                     // brasas
    g.add(box(0.14, 0.87, d, brick, -w / 2 + 0.07, 1.345, 0));                      // laterais de tijolo (y 0,91–1,78)
    g.add(box(0.14, 0.87, d, brick, w / 2 - 0.07, 1.345, 0));
    g.add(box(w - 0.28, 0.5, 0.1, brick, 0, 1.16, -d / 2 + 0.06));                  // fundo do fogo
    g.add(box(w - 0.28, 0.012, d - 0.18, M.steel, 0, 1.08, 0.02));                  // grelha
    g.add(box(w - 0.28, 0.37, 0.36, plaster, 0, 1.595, -d / 2 + 0.18));             // coifa (bloco junto à parede)
    g.add(put(box(w - 0.28, 0.45, 0.03, plaster, 0, 0, 0), 0, 1.595, 0.18, -0.613)); // frente inclinada da coifa
    g.add(box(0.4, 1.12, 0.34, plaster, 0, 2.34, -d / 2 + 0.18));                   // chaminé (y 1,78–2,90)
    g.add(box(0.52, 0.05, 0.46, granite, 0, 2.925, -d / 2 + 0.18));                 // tampa
    for (const sx of [-0.2, 0.15]) g.add(put(cyl(0.006, 0.006, 0.8, M.chrome, 0, 0, 0, 6), sx, 1.1, 0.02, Math.PI / 2)); // espetos
    g.add(box(0.1, 0.06, 0.2, M.red, -0.2, 1.12, -0.02));                            // carne no espeto
    place(g, 9.0, 4.595);   // fundo a 0,01 m da parede
  }

  // ---- cervejeira (geladeira de bebidas com porta de vidro) + caixinha de som ----
  {
    const g = G();
    g.add(box(0.56, 0.86, 0.5, M.dark, 0, 0.43, -0.03));
    g.add(box(0.56, 0.08, 0.1, M.dark, 0, 0.04, 0.24));                              // rodapé/piso interno
    g.add(box(0.5, 0.02, 0.07, ledCool, 0, 0.82, 0.255, { cast: false }));           // LED interno
    g.add(box(0.48, 0.015, 0.07, M.white, 0, 0.45, 0.255));                          // prateleira
    for (let i = 0; i < 2; i++) g.add(cyl(0.028, 0.028, 0.23, i ? amber : green, -0.1 + i * 0.2, 0.575, 0.255, 8));
    for (let i = 0; i < 2; i++) g.add(cyl(0.028, 0.028, 0.23, i ? green : amber, -0.08 + i * 0.16, 0.205, 0.255, 8));
    g.add(box(0.54, 0.78, 0.02, M.glass, 0, 0.47, 0.3, { cast: false, receive: false })); // porta de vidro
    g.add(cyl(0.01, 0.01, 0.5, M.chrome, 0.23, 0.5, 0.33, 6));                        // puxador
    g.add(box(0.16, 0.06, 0.07, navy, -0.1, 0.89, -0.05));                            // caixinha de som
    place(g, 9.98, 4.64);
  }

  // ---- mesa de madeira maciça com dois bancos (meio encaixados), no fundo direito: x 10,72–12,32 ----
  {
    const tx = 11.52, tz = 5.21;
    add(box(1.6, 0.045, 0.66, teak, tx, 0.757, tz));
    for (const dx of [-0.62, 0.62]) add(box(0.04, 0.73, 0.5, blk, tx + dx, 0.365, tz));
    add(box(1.2, 0.03, 0.03, blk, tx, 0.24, tz));
    for (const bz of [4.56, 5.86]) {
      add(box(1.4, 0.05, 0.3, teak, tx, 0.455, bz));
      for (const dx of [-0.55, 0.55]) add(box(0.03, 0.43, 0.24, blk, tx + dx, 0.215, bz));
    }
    add(cyl(0.16, 0.1, 0.09, M.white, tx, 0.825, tz, 16));                            // fruteira
    add(sph(0.05, M.red, tx - 0.05, 0.9, tz - 0.03)); add(sph(0.05, M.tan, tx + 0.06, 0.9, tz + 0.03));
    add(cyl(0.012, 0.035, 0.32, green, tx - 0.37, 0.94, tz - 0.16, 10));              // garrafa
    add(cyl(0.032, 0.026, 0.11, M.glass, tx + 0.33, 0.835, tz - 0.16, 10));
    add(cyl(0.032, 0.026, 0.11, M.glass, tx + 0.38, 0.835, tz + 0.17, 10));
  }

  // =====================================================================================
  // FAIXA DE GRAMA entre a varanda e o deck (z 6,2–7,2) e à esquerda do deck (x 2,4–2,9)
  // =====================================================================================
  // 22/11: removido a pedido do João (pisantes da porta ao deck); o deck continua até a faixa externa (z 6,2-7,2, x 2,9-10,9)
  { const ext = new THREE.Mesh(new THREE.PlaneGeometry(8.0, 1.0), M.deck); ext.rotation.x = -Math.PI / 2; ext.position.set(6.9, 0.02, 6.7); ext.receiveShadow = true; add(ext); }
  for (const x of [5.9, 9.3]) {                                                        // balizadores de jardim
    add(cyl(0.04, 0.04, 0.5, M.dark, x, 0.25, 6.7, 10));
    add(cyl(0.055, 0.055, 0.1, lampOn, x, 0.55, 6.7, 10));
  }
  // 22/11: removido a pedido do João (arbustos baixos do deck)

  // =====================================================================================
  // DECK DA PISCINA
  // =====================================================================================
  const POOL = ctx.POOL || { x0: 3.9, x1: 8.3, zc: 9.8, r: 1.6 };

  // ---- escadas de inox (corrimão curvo + 3 degraus) nas posições originais ----
  const ladder = () => {
    const g = G();
    for (const x of [-0.2, 0.2]) {
      g.add(cyl(0.02, 0.02, 1.5, M.chrome, x, 0.25, 0, 8));
      const bend = new THREE.Mesh(new THREE.TorusGeometry(0.25, 0.02, 8, 12, Math.PI / 2), M.chrome);
      bend.position.set(x, 1.0, -0.25); bend.rotation.set(0, Math.PI / 2, Math.PI / 2); bend.castShadow = true; g.add(bend);
    }
    for (const y of [-0.35, -0.05, 0.25]) g.add(box(0.4, 0.025, 0.06, M.chrome, 0, y, 0));
    return g;
  };

  // ---- espreguiçadeiras brancas com toalhas listradas, faixa sul do deck (z 11,7–12,4), viradas uma p/ outra ----
  const lounger = (fabric, towelA, towelB) => {
    const g = G();
    g.add(box(0.62, 0.04, 1.9, M.white, 0, 0.33, 0));
    for (const z of [-0.78, 0.78]) g.add(box(0.62, 0.3, 0.04, M.white, 0, 0.16, z));
    g.add(box(0.56, 0.07, 1.15, fabric, 0, 0.385, 0.33));
    g.add(put(box(0.56, 0.07, 0.72, fabric, 0, 0, 0), 0, 0.6, -0.6, 0.72));         // encosto reclinado (topo em -z)
    g.add(box(0.5, 0.02, 1.05, towelA, 0, 0.43, 0.3));                               // toalha estendida
    g.add(box(0.5, 0.024, 0.16, towelB, 0, 0.43, 0.55));                             // listra
    return g;
  };
  place(lounger(navy, M.white, navy), 4.75, 12.05, Math.PI / 2);
  place(lounger(navy, navy, M.white), 7.3, 12.05, -Math.PI / 2);
  // mesinha entre as espreguiçadeiras: toalha enrolada + protetor solar
  add(cyl(0.22, 0.22, 0.03, teak, 6.03, 0.45, 12.05, 20)); add(cyl(0.03, 0.03, 0.42, M.white, 6.03, 0.225, 12.05, 8)); add(cyl(0.16, 0.18, 0.02, M.white, 6.03, 0.01, 12.05, 16));
  add(put(cyl(0.06, 0.06, 0.28, navy, 0, 0, 0, 12), 6.03, 0.525, 12.0, 0, 0, Math.PI / 2));
  add(cyl(0.025, 0.025, 0.14, M.white, 6.14, 0.535, 12.15, 8));

  // 22/11: removido a pedido do João (guarda-sol, mastro, mesinha e caipirinhas)
  // ---- canto SE: 2 cadeiras de piscina e cooler ----
  {
    const poolChair = () => {                                                           // cadeira de piscina (tela marinho, tubo branco)
      const g = G();
      g.add(put(box(0.5, 0.03, 0.5, navy, 0, 0, 0), 0, 0.3, 0, -0.2));
      g.add(put(box(0.5, 0.03, 0.62, navy, 0, 0, 0), 0, 0.55, -0.3, 1.2));
      for (const sx of [-0.24, 0.24]) {
        g.add(rod(blk, 0.012, 0.012, sx, 0, 0.24, sx, 0.32, 0.22));
        g.add(rod(blk, 0.012, 0.012, sx, 0, -0.3, sx, 0.86, -0.42));
      }
      return g;
    };
    place(poolChair(), 9.4, 12.0, Math.PI);   // viradas para a piscina (-z)
    place(poolChair(), 10.65, 12.0, Math.PI);
    add(box(0.5, 0.4, 0.36, navy, 8.65, 0.2, 12.15)); add(box(0.52, 0.06, 0.38, M.white, 8.65, 0.43, 12.15)); // cooler
  }

  // 22/11: removido a pedido do João (mesa redonda, 4 cadeiras e lanterna)

  // ---- faixa oeste: ducha de piscina (chuveirão) sobre estrado de madeira, vaso grande, tocha ----
  {
    const x = 3.14, z = 9.55;
    add(box(0.6, 0.05, 0.6, teak, 3.28, 0.025, z));                                   // estrado
    add(cyl(0.025, 0.025, 2.2, M.chrome, x, 1.1, z, 10));                             // coluna
    add(box(0.3, 0.02, 0.02, M.chrome, x + 0.15, 2.15, z));                           // braço
    add(cyl(0.1, 0.1, 0.02, M.chrome, x + 0.28, 2.13, z, 16));                        // crivo
    add(put(cyl(0.03, 0.03, 0.04, M.chrome, 0, 0, 0, 10), x + 0.05, 1.0, z, 0, 0, Math.PI / 2)); // registro
  }
  // 22/11: removido a pedido do João (vasos spherePot/agavePot)
  const torch = (x, z) => {
    add(cyl(0.028, 0.032, 1.5, bamboo, x, 0.75, z, 8));
    add(cyl(0.07, 0.045, 0.16, M.dark, x, 1.58, z, 10));
    add(cyl(0, 0.05, 0.18, flame, x, 1.75, z, 8));
  };
  torch(3.25, 10.35); torch(3.35, 12.1); torch(7.0, 7.42);

  // ---- luzes subaquaticas embutidas nas paredes da piscina (reta + meia-lua), brilho turquesa ----
  {
    const dsk = (x, y, z, rx, rz) => { const d = cyl(0.07, 0.07, 0.02, aqua, x, y, z, 16); d.rotation.set(rx, 0, rz); d.castShadow = false; add(d); };
    const x0 = POOL.x0, x1 = POOL.x1, zc = POOL.zc, r = POOL.r;
    for (const x of [x0 + 0.7, (x0 + x1) / 2, x1 - 0.6]) { dsk(x, -0.75, zc - r + 0.02, Math.PI / 2, 0); dsk(x, -0.75, zc + r - 0.02, Math.PI / 2, 0); }
    for (const dz of [-0.55, 0.55]) dsk(x0 + 0.02, -0.75, zc + dz, 0, Math.PI / 2);
    for (const a of [-0.8, 0, 0.8]) { const m = cyl(0.07, 0.07, 0.02, aqua, x1 + Math.cos(a) * (r - 0.02), -0.75, zc + Math.sin(a) * (r - 0.02), 16); m.rotation.set(0, -a, Math.PI / 2); m.castShadow = false; add(m); }
  }

  // ---- tom turquesa translucido sobre a agua (mesmo contorno da piscina) + brilho das luzes subaquaticas ----
  {
    const r = POOL.r, sh = new THREE.Shape();
    sh.moveTo(POOL.x0, -(POOL.zc - r)); sh.lineTo(POOL.x1, -(POOL.zc - r));
    sh.absarc(POOL.x1, -POOL.zc, r, Math.PI / 2, -Math.PI / 2, true); sh.lineTo(POOL.x0, -(POOL.zc + r)); sh.closePath();
    const tint = new THREE.Mesh(new THREE.ShapeGeometry(sh, 32), new THREE.MeshBasicMaterial({ color: 0x35e0cf, transparent: true, opacity: 0.3, depthWrite: false }));
    tint.rotation.x = -Math.PI / 2; tint.position.y = -0.14; tint.renderOrder = 2; tint.userData.keep = true; add(tint);
    const cv = document.createElement('canvas'); cv.width = cv.height = 64;
    const cx = cv.getContext('2d'), gr = cx.createRadialGradient(32, 32, 0, 32, 32, 32);
    gr.addColorStop(0, 'rgba(200,255,250,0.95)'); gr.addColorStop(0.35, 'rgba(70,235,220,0.45)'); gr.addColorStop(1, 'rgba(40,220,210,0)');
    cx.fillStyle = gr; cx.fillRect(0, 0, 64, 64);
    const glowMat = new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(cv), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending });
    const glow = (x, z, s) => { const m = new THREE.Mesh(new THREE.PlaneGeometry(s, s), glowMat); m.rotation.x = -Math.PI / 2; m.position.set(x, -0.13, z); m.renderOrder = 3; add(m); };
    const x0 = POOL.x0, x1 = POOL.x1, zc = POOL.zc;
    for (const x of [x0 + 0.7, (x0 + x1) / 2, x1 - 0.6]) { glow(x, zc - r + 0.3, 1.1); glow(x, zc + r - 0.3, 1.1); }
    for (const dz of [-0.55, 0.55]) glow(x0 + 0.3, zc + dz, 1.0);
    for (const a of [-0.8, 0, 0.8]) glow(x1 + Math.cos(a) * (r - 0.3), zc + Math.sin(a) * (r - 0.3), 1.1);
  }

  // 22/11: boias, colchão inflável e bola removidos a pedido do João (piscina limpa como no vídeo)
}
