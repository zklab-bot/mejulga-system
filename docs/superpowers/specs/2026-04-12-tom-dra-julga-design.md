# Spec: Novo Tom da Dra. Julga — Observação Julgadora

**Data:** 2026-04-12
**Status:** Aprovado

---

## Problema

O tom atual da Dra. Julga produz posts formulaicos:
- Toda cena usa timestamps ("terça às 10h12") ou contagens exatas ("11 vídeos") como recurso de humor
- A estrutura "coleta de provas → escalada → veredicto" é previsível após 2 posts
- Jargão proibido ("Agravante:", "Reincidente.", "síndrome de...") escapa na geração
- Expressões elípticas incompletas quebram o humor ("como se nada")
- Mesmo título aparece em categorias diferentes

## Solução — Abordagem B: Frame de Observação Julgadora

### Mudança de frame

| Antes | Depois |
|---|---|
| Dra. Julga *conduz um processo*: coleta provas, escalada de evidências, profere sentença | Dra. Julga *observa e nomeia*: constata o comportamento com a secura de quem já viu tudo |
| Humor vem de dados e especificidade numérica | Humor vem do **reconhecimento** — o leitor pensa "isso sou eu" |
| Estrutura de cenas prescrita (cada cena tem papel fixo) | Cada cena é uma observação completa e autônoma |

### Exemplo do contraste

**Antes:** `"Terça, 10h12. Status no Slack: 'em foco profundo'. Você estava no terceiro episódio..."`

**Depois:** `"Você diz que está sem tempo. Mas tem tempo pra reclamar que está sem tempo. Isso já é tempo."`

---

## O que muda no SYSTEM_PROMPT

### Remove
- `REGRA DA ESPECIFICIDADE` — exigia âncoras numéricas por cena
- `REGRA DA ESCALADA` — prescrevia relação entre cenas
- `ÂNGULOS NARRATIVOS` — lista de 5 ângulos que viraram receita
- Exemplos com timestamps e referências a séries (O Urso)

### Adiciona ao TOM PROIBIDO
- Timestamps como recurso de humor ("às 23h47", "terça às 10h12")
- Contagens exatas como recurso de humor ("11 vídeos", "247 mensagens")
- `"Agravante:"` — fórmula gasta
- Frases elípticas incompletas ("como se nada", "aí fica lá")

### Mantém
- Nunca cruel
- Tom seco, entediado, autoridade natural
- Proibição de jargão médico e jurídico complexo
- Vocabulário simples permitido
- `"Gente,"` proibido

---

## Estrutura dos posts

- **6 cenas** (mantido — template visual é numerado para 6)
- Cenas 1–4: observações livres, cada uma fechada em si mesma
- Cena 5: veredicto (máximo 15 palavras, sem "Agravante:" ou "Reincidente.")
- Cena 6: CTA fixo (`mejulga.com.br`)

---

## Mudanças no validador

| Check | Mudança |
|---|---|
| Cena 5 max palavras | 20 → 15 |
| "Gente," | mantido |
| Jargão médico/jurídico | mantido + "Agravante:" adicionado |
| Frases elípticas | "como se nada" adicionado |
| Títulos repetidos | passa a checar cross-categoria (não só mesma categoria) |

---

## Mudanças em _INSTRUCOES_VEREDICTO

Remove templates rígidos com "Reincidente.", "Atenuante negado.", "Improváve.", estruturas de processo.
Substitui por orientações de tom com exemplos no novo estilo.
