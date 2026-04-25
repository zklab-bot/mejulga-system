const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const raw = fs.readFileSync(0, 'utf8');
const input = JSON.parse(raw);
const { roteiro, categoria, pasta_saida } = input;

const W = 1080, H = 1080;

const C = {
  creme:    '#F5F0E8',
  preto:    '#0D0D0D',
  dourado:  '#C8A97E',
  roxo:       '#534AB7',
  roxo_claro: '#8F88D9',
  vermelho: '#B03020',
  cinza:    '#8C8070',
  bege:     '#E8E0D0',
  cremedark:'#1A1410',
};

const BASE_CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,700;1,400;1,700&family=Instrument+Sans:wght@400;500;600&display=swap');
  * { margin:0; padding:0; box-sizing:border-box; }
  body { width:${W}px; height:${H}px; overflow:hidden; font-family:'Lora', serif; }
`;

function slideIntro(r) {
  const hook = (r.cenas && r.cenas[0] && r.cenas[0].texto_slide)
    ? r.cenas[0].texto_slide.replace(/\n/g, '<br>')
    : r.titulo || '';
  const proc  = r.numero_processo || '';
  const crime = r.crime || '';
  const titulo = r.titulo || '';

  return `<!DOCTYPE html><html><head><meta charset="utf-8"><style>
  ${BASE_CSS}
  body { background:${C.preto}; display:flex; flex-direction:column; position:relative; }
  .top-bar { height:72px; display:flex; align-items:center; justify-content:center; flex-shrink:0; border-bottom:1px solid #2a2a2a; }
  .top-bar span { font-family:'Instrument Sans',sans-serif; font-size:18px; font-weight:600; letter-spacing:5px; color:${C.roxo}; text-transform:uppercase; }
  .hook-zone { flex:1; display:flex; align-items:center; justify-content:center; padding:48px 72px; }
  .hook-text { font-family:'Lora',serif; font-size:64px; font-weight:700; color:${C.creme}; text-align:left; line-height:1.35; }
  .hook-text em { color:${C.dourado}; font-style:italic; }
  .left-accent { position:absolute; left:0; top:72px; width:6px; height:calc(100% - 72px - 140px); background:${C.roxo}; }
  .bottom-bar { height:140px; background:#0a0a0a; border-top:1px solid #1f1f1f; display:flex; flex-direction:column; justify-content:center; padding:0 52px; gap:6px; flex-shrink:0; }
  .meta-row { display:flex; align-items:center; gap:16px; }
  .meta-proc { font-family:'Instrument Sans',sans-serif; font-size:17px; color:#4a4a4a; letter-spacing:1px; }
  .meta-dot { width:4px; height:4px; border-radius:50%; background:#333; }
  .meta-crime { font-family:'Instrument Sans',sans-serif; font-size:17px; color:#4a4a4a; letter-spacing:0.5px; }
  .deslize { font-family:'Instrument Sans',sans-serif; font-size:20px; color:${C.dourado}; letter-spacing:2px; }
  .handle { position:absolute; top:24px; right:36px; font-family:'Instrument Sans',sans-serif; font-size:17px; color:#333; letter-spacing:1px; }
  </style></head><body>
  <div class="top-bar"><span>Dra. Julga &nbsp;·&nbsp; Caso Registrado</span></div>
  <div class="handle">@dra.julga</div>
  <div class="left-accent"></div>
  <div class="hook-zone"><div class="hook-text">${hook}</div></div>
  <div class="bottom-bar">
    <div class="deslize">Arrasta para o veredicto &nbsp;›</div>
    <div class="meta-row">
      <span class="meta-proc">${proc}</span>
      <div class="meta-dot"></div>
      <span class="meta-crime">${crime}</span>
    </div>
  </div>
  </body></html>`;
}

function slideCena(texto, numero, label, escuro) {
  const bg  = escuro ? C.preto    : C.creme;
  const fg  = escuro ? C.creme    : C.preto;
  const sub = escuro ? '#6a6058'  : C.cinza;
  const bar = escuro ? '#2a2a2a'  : C.bege;
  const acc = escuro ? C.roxo_claro : C.roxo;
  return `<!DOCTYPE html><html><head><meta charset="utf-8"><style>
  ${BASE_CSS}
  body { background:${bg}; display:flex; flex-direction:column; position:relative; }
  .left-bar { position:absolute; top:0; left:0; width:7px; height:${H}px; background:${acc}; }
  .header { display:flex; justify-content:space-between; align-items:center; padding:36px 52px 0 56px; }
  .counter { font-family:'Instrument Sans',sans-serif; font-size:20px; color:${sub}; letter-spacing:2px; }
  .handle  { font-family:'Instrument Sans',sans-serif; font-size:20px; color:${sub}; }
  .sep { height:1px; background:${bar}; margin:18px 44px 0; }
  .label-wrap { display:flex; align-items:center; gap:0; margin:28px 44px 0; }
  .label-line { flex:1; height:2px; background:${acc}; opacity:0.7; }
  .label-pill { background:${C.preto}; border-radius:100px; padding:10px 28px; margin:0 20px; white-space:nowrap; }
  .label-pill span { font-family:'Instrument Sans',sans-serif; font-size:20px; font-weight:600; letter-spacing:3px; color:${acc}; }
  .text-zone { flex:1; display:flex; align-items:center; justify-content:center; padding:36px 68px; }
  .main-text { font-family:'Lora',serif; font-size:56px; font-weight:700; color:${fg}; text-align:center; line-height:1.45; }
  .bottom-bar { background:${escuro ? '#080808' : C.cremedark}; height:88px; display:flex; align-items:center; justify-content:center; gap:18px; flex-shrink:0; position:relative; }
  .dot { width:10px; height:10px; border-radius:50%; background:${sub}; }
  .dot.active { background:${acc}; width:26px; border-radius:5px; }
  .rodape { position:absolute; bottom:14px; font-family:'Instrument Sans',sans-serif; font-size:15px; color:${sub}; }
  </style></head><body>
  <div class="left-bar"></div>
  <div class="header">
    <div class="counter">${numero} / 6</div>
    <div class="handle">@dra.julga</div>
  </div>
  <div class="sep"></div>
  ${label ? `<div class="label-wrap"><div class="label-line"></div><div class="label-pill"><span>${label}</span></div><div class="label-line"></div></div>` : ''}
  <div class="text-zone"><div class="main-text">${texto}</div></div>
  <div class="bottom-bar">
    ${[2,3,4,5].map(i=>`<div class="dot${i===numero?' active':''}"></div>`).join('')}
    <div class="rodape">@dra.julga</div>
  </div>
  </body></html>`;
}

function slideVeredicto(veredicto) {
  return `<!DOCTYPE html><html><head><meta charset="utf-8"><style>
  ${BASE_CSS}
  body { background:${C.creme}; display:flex; flex-direction:column; justify-content:space-between; padding:0; position:relative; }
  .stamp {
    position:absolute; top:28px; right:28px;
    width:118px; height:118px; border-radius:50%;
    border:4px solid ${C.vermelho};
    display:flex; align-items:center; justify-content:center;
    transform:rotate(-14deg); opacity:0.8;
  }
  .stamp-ring { position:absolute; inset:7px; border-radius:50%; border:1px dashed ${C.vermelho}; opacity:0.55; }
  .stamp-inner { display:flex; flex-direction:column; align-items:center; line-height:1.2; z-index:1; }
  .stamp-culpado { font-family:'Instrument Sans',sans-serif; font-size:9px; font-weight:600; color:${C.vermelho}; letter-spacing:3px; }
  .stamp-dra { font-family:'Lora',serif; font-size:13px; font-weight:700; color:${C.vermelho}; }
  .counter { font-family:'Instrument Sans',sans-serif; font-size:20px; color:${C.cinza}; margin-top:36px; letter-spacing:2px; }
  .martelo { font-size:44px; margin:14px 0 6px; }
  .vlabel-wrap { display:flex; align-items:center; gap:14px; width:calc(100% - 104px); }
  .vlabel-line { flex:1; height:2px; background:${C.dourado}; }
  .vlabel-text { font-family:'Instrument Sans',sans-serif; font-size:21px; font-weight:600; letter-spacing:4px; color:${C.preto}; white-space:nowrap; }
  .verdict-box { border:2px solid ${C.bege}; border-radius:20px; margin:16px 52px 0; padding:28px 44px; width:calc(100% - 104px); flex:1; display:flex; align-items:center; justify-content:center; }
  .verdict-text { font-family:'Lora',serif; font-size:64px; font-weight:700; color:${C.preto}; text-align:center; line-height:1.25; }
  .cta-box { background:${C.preto}; border-radius:20px; margin:14px 52px 20px; padding:32px 44px; width:calc(100% - 104px); display:flex; flex-direction:column; align-items:center; gap:10px; flex-shrink:0; }
  .cta1 { font-family:'Instrument Sans',sans-serif; font-size:26px; color:#d0c8bc; }
  .cta2 { font-family:'Lora',serif; font-size:32px; font-weight:700; color:white; text-decoration:underline; text-decoration-color:${C.dourado}; text-underline-offset:6px; }
  .cta-line { width:140px; height:2px; background:${C.dourado}; }
  .cta-url { font-family:'Lora',serif; font-size:42px; font-weight:700; color:${C.dourado}; }
  .dots-row { display:flex; gap:14px; padding:20px 0 28px; justify-content:center; flex-shrink:0; }
  .dot { width:10px; height:10px; border-radius:50%; background:${C.cinza}; }
  .dot.active { background:${C.dourado}; width:26px; border-radius:5px; }
  </style></head><body>
  <div class="stamp">
    <div class="stamp-ring"></div>
    <div class="stamp-inner">
      <div class="stamp-culpado">CULPADO</div>
      <div class="stamp-dra">DRA.</div>
      <div class="stamp-dra">JULGA</div>
    </div>
  </div>
  <div class="counter">6 / 6</div>
  <div class="martelo">🔨</div>
  <div class="vlabel-wrap">
    <div class="vlabel-line"></div>
    <div class="vlabel-text">VEREDICTO FINAL</div>
    <div class="vlabel-line"></div>
  </div>
  <div class="verdict-box"><div class="verdict-text">${veredicto}</div></div>
  <div class="cta-box">
    <div class="cta1">Esse foi o julgamento dos outros.</div>
    <div class="cta2">O seu é pior.</div>
    <div class="cta-line"></div>
    <div class="cta-url">mejulga.com.br</div>
  </div>
  <div class="dots-row">
    ${[1,2,3,4,5,6].map(i=>`<div class="dot${i===6?' active':''}"></div>`).join('')}
  </div>
  </body></html>`;
}

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.setViewportSize({ width: W, height: H });

  const saida = path.resolve(pasta_saida);
  fs.mkdirSync(saida, { recursive: true });

  const cenas = roteiro.cenas || [];
  const conclusao = roteiro.conclusao || roteiro.frase_printavel || '';
  const slides = [];
  const hoje = new Date().toISOString().slice(0,10);
  const LABELS = ['A ACUSAÇÃO', 'A PROVA', 'O AGRAVANTE', ''];

  async function shot(html, n) {
    await page.setContent(html, { waitUntil: 'networkidle' });
    const file = path.join(saida, `${hoje}_${categoria}_slide_0${n}.png`);
    await page.screenshot({ path: file });
    slides.push(file);
  }

  await shot(slideIntro(roteiro), 1);

  for (let i = 1; i < Math.min(cenas.length, 5); i++) {
    const texto = cenas[i].texto_slide || cenas[i].texto || '';

    // Pula cenas de veredicto — vão pro slide 6 via frase_printavel
    if (texto.toUpperCase().startsWith('VEREDICTO')) continue;

    const label = LABELS[i] || '';
    const escuro = (i % 2 === 0);
    await shot(slideCena(texto, i+1, label, escuro), i+1);
  }

  await shot(slideVeredicto(conclusao), 6);

  await browser.close();
  process.stdout.write(JSON.stringify(slides));
})();
