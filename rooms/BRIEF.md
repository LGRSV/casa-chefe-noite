# Brief — decoração detalhada por cômodo (Casa 3D, Three.js r170)

Você vai escrever UMA função JavaScript que decora um cômodo de uma casa modelada em Three.js
(cartão Lovelace do Home Assistant). O arquivo-fonte é `/Users/macbook/Public/casa-3d/casa3d-card.js`
(leia as partes relevantes: `ZONES`, `_buildWalls()` para portas/janelas, `furniture()` para as
peças prontas e `_buildFurniture()` para a colocação atual — que você vai SUBSTITUIR para o seu cômodo).

## Sistema de coordenadas (metros)
- X cresce para a direita, Z cresce para a frente (em direção à piscina/rua), Y para cima. Piso em y = 0.
- Paredes têm 0,15 m de espessura centradas nas linhas indicadas; pé-direito 2,8 m; NÃO há teto
  (vista de cima, estilo casinha de boneca). Luminárias pendentes ficam a y ≈ 2,55.
- Mantenha móveis a ≥ 0,08 m das paredes e fora do vão das portas (largura da porta + 0,9 m para abrir).

## Planta (ATUALIZADA 22/11, a pedido do João, que conhece a casa real)
- **O corredor/varanda NÃO EXISTE.** A faixa x 0–12,5 · z 4,2–6,2 é ÁREA EXTERNA ABERTA (rótulo visível 'Área externa'; id interno 'varanda' e item de luz 'externa' continuam). Piso igual ao do deck, sem forro, sem rodapé. NÃO há parede em z=6,2 entre x 2,4 e 12,5 (sem janela, vidro, porta nem verga). Só resta a parede norte do banheiro (x 0–2,4, z=6,2). A área externa segue até o deck/piscina (faixa de deck z 6,2–7,2, x 2,9–10,9). As paredes x=12,5 (z 0–6,2) e x=0 continuam.
- Parede frontal da casa (z=4,2): SEM portas. Só as janelas do quarto casal (x 2,5–3,3) e do quarto (x 5,5–6,4) e o vidro de correr da cozinha (x 9,6–12,2). O resto é parede cega (as antigas portas x 1,0–1,9, 4,1–5,0 e 7,4–8,3 foram fechadas).
- Portas internas NOVAS (vão 0,85 m, z 3,0–3,85): na parede x=3,6 (quarto casal e quarto) e na parede x=6,8 (quarto e sala/cozinha). Móveis afastados delas (cômoda do casal em z 2,2; cama do quarto em x 5,25; violão em z 1,5).
- Quarto casal: x 0–3,6 · z 0–4,2. Janela na parede do fundo (z=0) x 1,2–2,4. Janela frontal x 2,5–3,3. Porta interna em x=3,6 (z 3,0–3,85).
- Quarto/escritório: x 3,6–6,8 · z 0–4,2. Janela fundo x 4,4–5,6. Janela frontal x 5,5–6,4. Portas internas em x=3,6 e x=6,8 (z 3,0–3,85). TV na parede x=6,8 (z 1,6–2,6, y 1,1–1,8) — é um objeto do cartão, NÃO recrie.
- Sala/cozinha: x 6,8–10,3 · z 0–4,2. Sem porta na frente; entra-se pela porta interna do quarto (x=6,8) e pelo vidro da cozinha. Ar-condicionado em (7,6, 2,35, 0,2) — objeto do cartão, NÃO recrie. SEM divisória em x=10,3 (22/11): sala e cozinha integradas. Rótulo na interface: 'Sala' (id sala). Mesa de jantar de madeira clara NA SALA, oval 1,7 × 0,95 em (9,2 · 3,4) com 6 cadeiras. Balcão de cozinha (península com banquetas) em frente à geladeira (centro x 9,8 · z 1,9), geladeira em (9,8 · 0,45).
- Cozinha (id interno 'balcao', rótulo 'Cozinha'): armários, pia, fogão e coifa; SEM mesa (a mesinha de 3 cadeiras saiu em 22/11), x 10,3–12,5 · z 0–4,2. Janela fundo x 11,0–12,0. Vidro para fora (z=4,2) x 9,6–12,2.
- Área externa (ex-varanda): x 0–12,5 · z 4,2–6,2, aberta. Mobília solta que fica: rede, sofá, churrasqueira e cervejeira encostadas em z=4,2, mesa de madeira com bancos (x 10,7–12,3). Saíram: capacho e pisantes da porta.
- Banheiro: x 0–2,4 · z 6,2–8,8. Porta na parede x=2,4, z 7,0–7,9.
- Dispensa: x 0–2,4 · z 8,8–10,6. Porta na parede x=2,4, z 9,3–10,1.
- Garagem: x 0–3,0 · z 10,6–16,0. Vão aberto para o quintal na parede x=3,0 (z 11,4–15,4). Portão na parede z=16 (x 0,3–2,7). O carro (VW up! branco) fica centrado em (1,5, 13,6) — NÃO recrie, deixe o espaço.
- Deck da piscina: x 2,9–10,9 · z 7,2–12,4. Piscina: reta x 3,9–8,3 + meia-lua até x 9,9; z 8,2–11,4. A bomba (caixa em 11,35, 12,9) é objeto do cartão.
- Jardim (grama): x 10,9–13,4 · z 6,2–12,4; muro em x=13,4 com duas arandelas (y 2,0) em z 8,4 e 11,4. Pátio (asfalto): x 2,4–13,4 · z 12,4–16,0 (22/11: sem demarcação branca de vaga nem calço de roda; só o piso). Muro frontal z=16,0 contínuo (22/11: portãozinho de pedestre x 5,6–6,6 fechado a pedido do João; sem caixa de correio). Removidos a pedido do João (22/11): guarda-sol, mesa redonda e TODAS as plantas da casa inteira, dentro e fora (árvores, arbustos, palmeiras, vasos, folhagens, temperos, ramos; F.plant e F.tree saíram do motor); grama e caminho de pedras ficam.

## API disponível no `ctx` (não importe nada; não use globais)
- `ctx.THREE` — namespace do Three.js r170 (Shape, ExtrudeGeometry, TorusGeometry, LatheGeometry, Group, Mesh, MeshStandardMaterial, Color…).
- `ctx.box(w, h, d, mat, x, y, z, opts?)` → Mesh caixa centrada em (x, y, z). `opts.cast=false` / `opts.receive=false` desligam sombra.
- `ctx.cyl(rTop, rBottom, h, mat, x, y, z, seg=16, open=false)` → cilindro/cone centrado.
- `ctx.sph(r, mat, x, y, z)` → esfera.
- `ctx.place(group, x, z, ry=0, y=0)` → posiciona um Group (origem no centro da base) e adiciona à cena. Devolve o group.
- `ctx.add(mesh)` → adiciona um Mesh solto à cena (equivale a scene.add). NUNCA faça `ctx.add(x).rotation = …` — `add` devolve a cena.
- `ctx.std({ color, roughness, metalness, emissive, emissiveIntensity, transparent, opacity })` → novo MeshStandardMaterial.
- `ctx.rnd()` → aleatório determinístico (0–1), já semeado para o seu cômodo.
- `ctx.M` — materiais prontos: wall, lowWall, deck, basin, door, glass (vidro translúcido), wood, woodLite, woodDark, white, steel, chrome, dark, mattress, red, blue, navy, tan, chair, cushion, plant, leaf2, pot, trunk, soil, car, tire, mirror, screenOff, lightRed, lightWhite, book (array de 6 cores).
- `ctx.F` — peças prontas (cada uma devolve um Group com origem no centro da base; use com `ctx.place`):
  bed(w, l, blanketMat) [cabeceira em -z] · nightstand(lamp=true) · wardrobe(w, h=2, d=0.6, doors=2) · desk(w, d, withMonitor=true) ·
  officeChair() · bookshelf(w, h, d=0.3, levels=4, seed=1) · sofa(w, d, fabricMat) [encosto em -z] · diningTable(rx, rz) · chair(fabricMat) [encosto em -z] ·
  fridge() · stove() · hood() · cabinet(w, h, d, doors, mat?) · sink(w=0.5, d=0.4) · toilet() [caixa em -z] · shower(s) [vidro em +x e +z] · washbasin() [espelho em -z] ·
  shelves(w, h, d, levels, seed) · plant(size=1, seed=1) · tree() · ladder() · lounger(fabricMat) · parasol() · roundTable(r=0.45) · rug(w, d, colorHex).

## Regras
1. Escreva APENAS a função `function room<Nome>(ctx) { … }` no arquivo indicado (sem import/export, sem código fora da função, sem `console.log`). ES2020 válido.
2. Só primitivas e materiais; nada de texturas externas, nada de fetch, nada de luzes (PointLight/SpotLight etc. — o cartão já cuida da iluminação).
3. Orçamento: até ~150 meshes no cômodo. Prefira criar builders locais (funções dentro da sua função) para peças repetidas.
4. Sombras: os helpers já ligam cast/receive. Vidro/objetos finos: `{ cast: false }`.
5. Objetos do cartão (TV, ar-condicionado, bomba, carro, luminárias) NÃO devem ser recriados nem cobertos.
6. Verifique a sintaxe antes de terminar: `osascript -l JavaScript /caminho/do/arquivo.js` (deve sair sem erro; JavaScriptCore).
7. Capriche em detalhe realista e coerente com uma casa brasileira de classe média (ex.: churrasqueira na varanda, rede, tanque na área de serviço, etc.), mas com bom gosto: paleta discreta (madeira, branco, cinza, um acento de cor por cômodo).
8. No fim, responda com: (a) o caminho do arquivo, (b) lista curta do que você colocou, (c) qualquer dúvida/limitação.

## Modo 3D estático (22/11)
Opção `static_view` do cartão (padrão false; a demo usa true): tocar num cômodo só seleciona e abre os controles, sem voo/zoom (`_focusRoom`) e sem giro automático (`_autoOrbitOk`); arrastar para girar continua.
