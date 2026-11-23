# Render final: arte aprovada (v4b)

Máquina: i5-10400, sem placa de vídeo, 7,8 GB de RAM. Rode **um Blender por vez** e feche os outros programas
antes de começar (confira com `Get-Process blender`). Todos os caminhos de saída são absolutos.
Rode tudo em PowerShell, a partir da raiz do repositório.

## Amostras escolhidas (cerca de 1 h 35 min no total)

| Peça | Tamanho | Amostras | Tempo estimado |
|---|---|---|---|
| Maquete (base, cômodos e noite) | 2880x1800, em 6 faixas | 64 | cerca de 13 min, com a costura |
| Giro | 8 quadros de 1920x1200 | 64 | cerca de 11 min |
| Voo, computador | 72 quadros de 1920x1200 | 36 | cerca de 70 min |
| Voo, celular | 72 quadros de 1280x800 | 0 (reduzidos dos de 1920) | menos de 1 min |

A amostragem adaptativa (limiar 0,01) costuma baixar esses tempos.

## 0. Preparação

```powershell
$B = "C:\Users\JOAO ANTONIO LAGARES\apps\blender\blender-4.5.16-windows-x64\blender.exe"
$R = "C:\Users\JOAO ANTONIO LAGARES\repos\casa-chefe-noite"
$F = "$R\render\saida_final"
Get-Process blender -ErrorAction SilentlyContinue   # tem que vir vazio
```

## 1. Maquete: `main`, 2880x1800, 64 amostras, 6 faixas

Uma faixa por vez. Na resolução cheia a imagem inteira não cabe na RAM.

```powershell
foreach ($k in 0..5) {
  $env:STRIP = "$k/6"
  & $B -b -P "$R\render\montar_v4.py" -- main 64 1.0 "$F\faixas\s$k" | Select-String "TEMPO|Error"
}
Remove-Item Env:STRIP
python "$R\render\costurar_v4.py" "$F\faixas" 6 "$F\maquete"
```

A pasta `$F\maquete` recebe `base.png`, um PNG por cômodo, `noite.png` e `pontos.json` (2880x1800). A costura
mistura 48 px de sobreposição entre as faixas e aplica saturação 1,04, brilho nas lâmpadas e vinheta.

## 2. Giro: 8 quadros de 1920x1200, 64 amostras, sem ampliar

```powershell
& $B -b -P "$R\render\montar_v4.py" -- giro 64 1.0 "$F\giro" | Select-String "giro|TEMPO"
```

## 3. Voo: 72 quadros de 1920x1200, 36 amostras, em `intro\quadros`

```powershell
& $B -b -P "$R\render\montar_intro_v2.py" -- 72 1920x1200 36 "$R\intro\quadros" | Select-String "quadro|TEMPO"
```

Esse passo também grava `intro\caminho.json`. Se a execução parar no meio, retome do quadro que faltou, por
exemplo do 41 ao 72:

```powershell
& $B -b -P "$R\render\montar_intro_v2.py" -- 72 1920x1200 36 "$R\intro\quadros" 41 72
```

Os quadros saem em JPEG q92. Confira que o último termina no fundo da página: o canto de `intro_072.jpg` deve
dar (13,23,48), contra o alvo #0e1630 = (14,22,48).

## 4. Voo para celular: 72 quadros de 1280x800 em `intro\quadros_m`

```powershell
python "$R\render\quadros_celular.py" "$R\intro\quadros" "$R\intro\quadros_m"
```

Os quadros do celular são reduzidos dos de 1920 com Lanczos, em JPEG q88. Ficam mais nítidos do que um render
próprio a 1280 e não gastam Blender. O `intro\intro.js` usa `intro/quadros_m/` quando a tela tem menos de
900 px e `intro/quadros/` no computador. Se a pasta do celular não existir, ele volta para a do computador.

## 5. WebP e giro da página: qualidade 90, sem curva de gama

```powershell
python "$R\render\gerar_webp.py" "$F\maquete" "$F\giro"
```

O script grava em `render\web\` os arquivos `base.webp`, um `<cômodo>.webp` por cômodo e `noite.webp`, todos
em 2880x1800, RGBA e qualidade 90. Também copia `giro_01..08.jpg` em 1920x1200, sem ampliar.

**Não aplique gama nem clareamento.** O antigo `webp_gen.py` fazia `rgb ** 0.5` no `base`, e isso não vale
mais: a base v4 já sai exposta pela luz (estúdio `EST_K=1.5`).

O script imprime os pontos (`xr`, `yr`) de cada cômodo. A câmera não mudou, então eles devem bater com o `PTS`
do `demo.template.html`. Se algum mudar, atualize o `PTS` e rode `python build.py`.

## 6. Conferir e publicar

1. Abra `index.html` e confira a maquete (base, cômodos acesos e giro) e o voo, no computador e numa janela
   com menos de 900 px.
2. Faça o commit no ramo `design-noite`. O push quem faz é o João.

## O que mudou na arte (v4b, aprovado)

- **Elipse clara no piso da varanda.** Não era um tapete: era a vinheta do compositor. A Ellipse Mask com
  Blur do Blender 4.5 saía com borda dura. Agora a vinheta é uma imagem gerada com a mesma fórmula do
  `costurar_v4.py`.
- **Cor.** A cena estava laranja demais. Agora:
  - luzes dos cômodos em cerca de 3000 K, com cor linear (1, 0,62, 0,32);
  - luz principal e sol mais neutros;
  - luz de recorte fria, como luar, para separar a maquete do fundo;
  - saturação 1,04, antes 1,12.
- **Piso de tábuas.** Tom de carvalho-mel, sem o rosado. Juntas em relevo e acabamento acetinado, com
  rugosidade de 0,38 a 0,55.
- **Pretos.** Viraram grafite (0,028), com reflexo, em vez de buracos pretos de jogo.
- **Cúpulas das luminárias.** Não fazem mais sombra, para não recortarem a luz em cone no piso.
- **Bevel.** Fica de fora em planos sem espessura (pisos e decalques). O carro Node_64 não foi tocado.
- **Piscina.** Cáusticas em células menores e mais suaves.
- **Giro.** O estúdio ficou em 0,4 (`GIRO_K`), antes 0,3: continua noite, mas a casa fica legível.
