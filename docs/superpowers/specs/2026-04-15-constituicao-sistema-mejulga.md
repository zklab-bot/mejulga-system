# Constituição do Sistema Me Julga

**Data:** 2026-04-15  
**Escopo:** Arquitetura completa de skills/agentes para o sistema de geração de conteúdo da Dra. Julga  
**Status:** Aprovado para implementação

---

## Visão Geral

O sistema Me Julga atualmente tem a camada de distribuição funcionando (geração de imagens, post no Instagram, engajamento), mas não tem uma "constituição" — regras e personas que garantam consistência de voz, qualidade de hook e relevância de conteúdo.

Este documento define 14 skills organizadas em 4 fases. Cada skill é um arquivo de regras/prompt que alimenta o gerador de conteúdo.

---

## Princípio Central

> Skills 01, 02 e 03 são carregadas como **contexto de fundo** em todas as execuções. Não são "passos" — são o pressuposto silencioso de tudo que o sistema gera.

---

## Fase 1 — Alma (quem é a Dra. Julga)

Bloqueante para todas as fases seguintes. Sem isso, qualquer conteúdo gerado pode soar errado de formas que não são detectáveis por checklist.

### Skill 01 — Persona da Dra. Julga
**Arquivo:** `content-engine/skills/persona.md`

Define a voz, o tom, o vocabulário e o worldview da personagem.

- Tom: clínico, frio, observacional — nunca emocional
- Frases características e padrões de construção de sentença
- Vocabulário jurídico próprio da Dra. Julga
- Ritmo: frases curtas, cortantes, sem adjetivos desnecessários
- Como ela abre um caso, como fecha
- Como ela trata o réu (distância calculada, não hostilidade)

### Skill 02 — Anti-Persona
**Arquivo:** `content-engine/skills/anti_persona.md`

O que a Dra. Julga explicitamente não é. Evita deriva de tom ao longo do tempo.

- Não é coach de vida — não dá conselhos
- Não é empática nem acolhedora
- Não moraliza — apenas constata
- Não explica o "porquê" emocional — julga o comportamento
- Lista de frases proibidas com alternativas corretas

### Skill 03 — Código de Julgamento
**Arquivo:** `content-engine/skills/codigo_julgamento.md`

As regras de como ela constrói um veredicto válido.

- Estrutura obrigatória: acusação → provas numeradas → veredicto
- Tipos de veredicto: Culpado, Culpado com atenuante, Sem provas suficientes (raro), Reincidente
- Como graduar a gravidade do crime por categoria
- O que conta como prova válida (comportamento observável, específico, com horário/data)
- Formato do número de processo: `[CAT]-[NNN]/[AA]`

---

## Fase 2 — Criativa (como ela cria conteúdo)

Depende da Fase 1. Define qualidade e consistência de cada post.

### Skill 04 — Regras de Hook
**Arquivo:** `content-engine/skills/hook_rules.md`

Os 21 templates de hook com instrução de uso.

**Grupos:**
- V1–V8: Verdade Inconveniente (foco principal)
- L1–L7: Loop de Curiosidade
- C1–C6: Combinadas (Verdade + Loop)

**Regras de aplicação:**
- Nunca repetir o mesmo template nos últimos 7 posts
- Mapeamento de template recomendado por categoria
- Hook da capa deve criar razão para swipe (não apenas parar o scroll)
- Slide 2 aprofunda a tensão aberta na capa — nunca resolve

### Skill 05 — Estrutura de Slides
**Arquivo:** `content-engine/skills/estrutura_slides.md`

O papel de cada slide no carrossel.

| Slide | Função | Regra |
|---|---|---|
| 1 | Hook — para o scroll + convida swipe | Máx. 12 palavras. Cria tensão aberta. |
| 2 | Hook 2 — aprofunda a tensão | Não resolve o slide 1. Adiciona camada. |
| 3–5 | Provas numeradas | Específicas, com detalhe absurdo de horário/contexto |
| 6 | Veredicto | Uma linha. Sem explicação. |
| 7 | CTA | mejulga.com.br + frase curta da Dra. Julga |

### Skill 06 — Constituição Visual
**Arquivo:** `content-engine/skills/visual_rules.md`

Regras de design que garantem que a capa pare o scroll antes do texto.

- Regras de fundo por tipo de hook (escuro para evidência, claro para acusação)
- Hierarquia tipográfica por slide
- Máximo de 12 palavras por slide
- Quando quebrar o padrão visual intencionalmente
- Regras para o slide de veredicto (destaque, espaço negativo)

### Skill 07 — Regras de Legenda
**Arquivo:** `content-engine/skills/legenda_rules.md`

Como a legenda do Instagram é escrita.

- Abertura: espelha o hook da capa (1–2 linhas)
- Corpo: 1–2 linhas no tom da Dra. Julga
- CTA: sempre direciona para mejulga.com.br
- Hashtags: pool por categoria + 3 fixas (#DrJulga #MeJulga #Veredicto)
- Nunca usa emojis no corpo — apenas no CTA se necessário

### Skill 08 — Filtro de Sensibilidade
**Arquivo:** `content-engine/skills/filtro_sensibilidade.md`

Checklist pré-publicação automático.

- Temas proibidos: saúde mental grave, suicídio, violência, política
- Nível de agressividade aceitável: irônico, nunca cruel
- Gatilhos que forçam aprovação manual antes de publicar
- Categorias que sempre exigem revisão humana (saúde_mental)

---

## Fase 3 — Inteligência (o que alimenta o conteúdo)

Depende da Fase 2. Garante relevância e variedade.

### Skill 09 — Memória de Conteúdo
**Arquivo:** `content-engine/skills/memoria.md` + `content-engine/generated/memoria_estado.json`

Evita repetir hooks, casos e ângulos recentes.

- Registra: hook usado, categoria, tema central, número de processo
- Janela de memória: últimos 21 posts (3 semanas)
- Garante que cada template V/L/C seja usado antes de repetir
- Formato JSON atualizado após cada publicação

### Skill 10 — Calendário Cultural
**Arquivo:** `content-engine/skills/calendario_cultural.md`

Datas e eventos que geram casos automáticos.

- Mapa anual de datas → categorias recomendadas
- Antecipação: gera conteúdo 3 dias antes da data
- Eventos nacionais relevantes (Carnaval, Copa, etc.)
- Eventos semanais fixos (domingo 18h → saúde_mental, segunda → trabalho)

### Skill 11 — Google Trends Agent
**Arquivo:** `content-engine/skills/trends_agent.md`

Lê o que está em alta e converte em caso da Dra. Julga.

- Busca trends diários filtrados por relevância para as 7 categorias
- Mapeamento: trend → categoria → ângulo de julgamento
- Filtro: descarta trends de política, tragédias, polêmicas graves
- Output: tema sugerido + categoria + hook recomendado

### Skill 12 — Estratégia de Crescimento
**Arquivo:** `content-engine/skills/estrategia_crescimento.md`

Regras de frequência, horário e mix de formatos por semana.

- Posts por semana por categoria (balanceamento)
- Sequência de hooks na semana (não repetir tipo no dia seguinte)
- Horários ótimos por categoria
- Mix semanal: carrossel / reel / verdict card

---

## Fase 4 — Feedback (o que melhora o sistema)

Depende de dados reais publicados. Fecha o loop evolutivo.

### Skill 13 — Performance Agent
**Arquivo:** `content-engine/skills/performance_agent.md`

Lê métricas do Instagram e identifica o que funciona.

- Roda toda segunda-feira
- Métricas: impressões, swipe rate, saves, comentários
- Cruza com memória: qual hook estava em cada post
- Atualiza peso dos hooks nas Regras de Hook
- Envia relatório via Telegram: top 3 posts, pior performance, recomendação

### Skill 14 — A/B de Hooks
**Arquivo:** `content-engine/skills/ab_hooks.md`

Testa o mesmo caso com 2 hooks diferentes.

- Mesmo tema/categoria, 2 templates distintos
- Publicação escalonada: versão A (dia 1), versão B (dia 4)
- Comparação após 48h de cada post
- Registra vencedor na Memória (Skill 09)
- Hook vencedor sobe de prioridade na rotação

---

## Fluxos de Execução

### Fluxo 1 — Geração de Post (diário)
```
Trigger → Skill 09 (lê memória) → Skill 12 (estratégia)
→ Skill 10/11 (tema) → Skill 04 (hook) → Skill 03 (caso)
→ Skill 05 (slides) → Skill 06 (visual) → Skill 07 (legenda)
→ Skill 08 (filtro) → [aprovação humana opcional]
→ gerar_carrossel.py → post_carrossel_instagram.py
→ Skill 09 (atualiza memória)
```

### Fluxo 2 — Performance Semanal (toda segunda)
```
Trigger → Skill 13 (lê métricas) → Skill 09 (cruza com memória)
→ Skill 13 (identifica padrões) → Skill 04 (atualiza pesos)
→ Skill 12 (ajusta estratégia) → relatório Telegram
```

### Fluxo 3 — A/B de Hooks (sob demanda)
```
Trigger → Skill 04 (seleciona 2 hooks) → Skill 14 (gera versão A)
→ Skill 14 (gera versão B) → aprovação humana
→ posta A (dia 1) → posta B (dia 4)
→ Skill 13 (compara após 48h cada) → Skill 09 (registra vencedor)
```

---

## Localização dos Arquivos

```
content-engine/
└── skills/
    ├── persona.md              (Skill 01)
    ├── anti_persona.md         (Skill 02)
    ├── codigo_julgamento.md    (Skill 03)
    ├── hook_rules.md           (Skill 04)
    ├── estrutura_slides.md     (Skill 05)
    ├── visual_rules.md         (Skill 06)
    ├── legenda_rules.md        (Skill 07)
    ├── filtro_sensibilidade.md (Skill 08)
    ├── memoria.md              (Skill 09)
    ├── calendario_cultural.md  (Skill 10)
    ├── trends_agent.md         (Skill 11)
    ├── estrategia_crescimento.md (Skill 12)
    ├── performance_agent.md    (Skill 13)
    └── ab_hooks.md             (Skill 14)
```

---

## Ordem de Construção

1. Skill 01 — Persona ← **começar aqui**
2. Skill 02 — Anti-Persona
3. Skill 03 — Código de Julgamento
4. Skill 04 — Regras de Hook
5. Skill 05 — Estrutura de Slides
6. Skill 06 — Constituição Visual
7. Skill 07 — Regras de Legenda
8. Skill 08 — Filtro de Sensibilidade
9. Skill 09 — Memória de Conteúdo
10. Skill 10 — Calendário Cultural
11. Skill 11 — Google Trends Agent
12. Skill 12 — Estratégia de Crescimento
13. Skill 13 — Performance Agent
14. Skill 14 — A/B de Hooks
