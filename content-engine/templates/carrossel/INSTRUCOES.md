# Templates de Carrossel — Dra. Julga

Coloque aqui os fundos criados no Canva. O código detecta automaticamente os arquivos e os usa como base — sobrepondo o texto do roteiro por cima.

---

## Arquivos esperados

| Arquivo | Slide | Descrição |
|---|---|---|
| `intro_bg.png` | Slide 1 | Fundo da intro ("ME JULGA") |
| `cena_bg.png` | Slides 2–5 | Fundo das cenas (reutilizado em todos) |
| `veredicto_bg.png` | Slide 6 | Fundo do veredicto |

Se qualquer arquivo estiver faltando, o sistema usa o design gerado automaticamente em branco.

---

## Formato dos arquivos

- **Tipo:** PNG
- **Dimensões:** 1080 × 1080 px
- **Modo de cor:** RGB (não use CMYK)
- **Exportar do Canva:** Compartilhar → Baixar → PNG → 1080 × 1080

---

## Onde o código coloca o texto

O código sobrepõe texto nas seguintes áreas. **Deixe essas regiões limpas no Canva** (sem elementos que dificultem a leitura):

### `intro_bg.png`
```
┌─────────────────────────┐
│  [contador: "1/6"]      │  ← y = 0–60 (sutil)
│  [ícone balança]        │  ← y = 60–180
│  [ME JULGA]             │  ← y = 250–320 (texto grande)
│  [sublinhado]           │  ← y = 324
│                         │
│  [texto da intro]       │  ← y = 380–620
│                         │
│                         │
│  [badge "Deslize >>>"]  │  ← y = 795–860 (borda roxa)
│  [@dra.julga]           │  ← y = 1050–1080 (pequeno)
└─────────────────────────┘
```
**Zona segura para design:** bordas laterais (0–80px e 1000–1080px) e faixas horizontais acima de y=240 e abaixo de y=870.

---

### `cena_bg.png`
```
┌─────────────────────────┐
│  [contador]             │  ← y = 0–40
│  [PROVA Nº 1]           │  ← y = 50–110 (pill roxa)
│  [linha separadora]     │  ← y = 122
│                         │
│                         │
│  [texto da cena]        │  ← y = 350–700 (centralizado)
│                         │
│                         │
│  [● ○ ○ ○ ○ ○]          │  ← y = 1020–1045 (dots)
│  [@dra.julga]           │  ← y = 1055–1080
└─────────────────────────┘
```
**Zona segura para design:** bordas laterais e muito sutil no centro (use transparência ou cor bem clara).

---

### `veredicto_bg.png`
```
┌─────────────────────────┐
│  [contador]             │  ← y = 0–40
│  [ícone martelo]        │  ← y = 60–130
│  [VEREDICTO FINAL ——]   │  ← y = 155–180
│                         │
│  ┌─── caixa cinza ───┐  │  ← y = 205–610
│  │ [texto veredicto] │  │
│  │  + carimbo CULPADO│  │
│  └───────────────────┘  │
│  ┌─── bloco CTA ─────┐  │  ← y = 638–870 (sempre escuro)
│  │  mejulga.com.br   │  │
│  └───────────────────┘  │
│  [dots + @dra.julga]    │  ← y = 1020–1080
└─────────────────────────┘
```
**Zona segura para design:** bordas laterais e área abaixo de y=870 (mas o código já cobre essa região com dots).

---

## Dica de design no Canva

- Use cores de fundo sólidas ou gradientes suaves (evite padrões no centro)
- Elementos decorativos (bordas, ícones de marca) ficam bem nas bordas e cantos
- Deixe o centro do slide **limpo** — o texto precisa de contraste para ser legível
- Se usar cor de fundo escura, **informe** para que o código ajuste as cores do texto automaticamente

---

## Como ativar

Basta salvar os 3 arquivos PNG nesta pasta. O código detecta automaticamente na próxima execução.

Para testar localmente:
```bash
cd content-engine
python gerar_carrossel.py --categoria amor
```
