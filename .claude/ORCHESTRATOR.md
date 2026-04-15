# Orchestrator — mejulga-system

## Visão geral
Este documento explica como as skills se conectam e quando
usar cada uma durante uma sessão de Claude Code.

## Ordem de leitura obrigatória
Sempre leia nessa sequência antes de qualquer tarefa:

1. CLAUDE.md → visão geral técnica e comandos
2. skills/01-contexto.md → o que é o projeto
3. skills/02-persona.md → quem é a Dra. Julga
4. skills/03-conteudo.md → o que e como produzir
5. skills/04-processos.md → como executar
6. skills/05-restricoes.md → o que nunca fazer

## Quando usar cada skill

### Tarefas de geração de conteúdo

#### Skills carregadas automaticamente pelo loader (content-engine/skills/)
1. `persona.md` — voz, tom, ritmo, vocabulário da Dra. Julga
2. `anti_persona.md` — limites: o que ela nunca faz
3. `codigo_julgamento.md` — estrutura acusação → provas → veredicto
4. `hook_rules.md` — grupos E, D, V, L, C + mapeamento categoria→hook
5. `estrutura_slides.md` — papel de cada cena + regra do slide visual
6. `legenda_rules.md` — legenda, CTA, hashtags

#### Fluxo de geração (python generate_reels.py --categoria X)
1. `loader.py` assembla skills 1–6 em system prompt (~16k chars)
2. `generate_reels.py` seleciona hook por categoria via `_HOOK_POR_CATEGORIA`
3. Prompt instrui cenas por grupo (E→D→provas→veredicto→CTA)
4. Validador rejeita: slide=narração longa, jargão, fórmulas gastas, veredicto longo
5. Máximo 2 tentativas; na 2ª falha passa para revisão manual

#### Hierarquia de hook por cena
| Cena | Grupo | Função |
|------|-------|--------|
| 1 | E (Exposição Direta) | Flagrante com dado concreto — para o scroll |
| 2 | D (Diagnóstico Frio) | Verdade clínica sem consolação — aprofunda |
| 3–4 | Provas | Comportamentos observáveis, escalada progressiva |
| 5 | Veredicto A/B/C | Sentença seca, máx 15 palavras |
| 6 | CTA fixo | mejulga.com.br |

#### Mapeamento categoria → hook (fonte: hook_rules.md)
| Categoria | Cena 1 | Cena 2 |
|-----------|--------|--------|
| trabalho | E1 | D1 |
| amor | E1 | D3 |
| dinheiro | E1 | D2 |
| dopamina | E3 | D1 |
| vida_adulta | E2 | D3 |
| social | E1 | D1 |
| saude_mental | V1 | D1 |

### Tarefas de desenvolvimento técnico
Skills obrigatórias: 01 + 04 + 05
- Alterar pipeline de publicação
- Modificar render_slides.py
- Configurar GitHub Actions
- Integrar nova API

### Tarefas de criação de nova skill
Skills obrigatórias: todas
- Identificar gap no sistema atual
- Escrever nova skill no formato padrão
- Adicionar em .claude/skills/
- Referenciar neste ORCHESTRATOR.md

### Tarefas de troubleshooting
Skills obrigatórias: 04 + 05
- Pipeline falhando
- Post não publicando
- Actions não disparando

## Fluxo de sessão recomendado

### Início de sessão
1. Lê CLAUDE.md + skills relevantes para a tarefa
2. Verifica status do último workflow no GitHub Actions
3. Confirma categoria do dia na rotação

### Durante a sessão
- Mantém tom da Dra. Julga em qualquer conteúdo gerado
- Registra decisões técnicas no CLAUDE.md
- Não altera templates sem verificar dimensões

### Fim de sessão
1. Atualiza próximos passos no CLAUDE.md
2. Commita com mensagem descritiva
3. Verifica se webhook zklab-os sincronizou

## Estrutura de arquivos
mejulga-system/
├── CLAUDE.md
├── ORCHESTRATOR.md
├── .claude/
│   └── skills/
│       ├── 01-contexto.md
│       ├── 02-persona.md
│       ├── 03-conteudo.md
│       ├── 04-processos.md
│       └── 05-restricoes.md
├── render_slides.py
├── post_carrossel_instagram.py
└── .github/
└── workflows/
└── daily_post.yml

## Evolução do sistema
Quando criar nova skill:
1. Identifica a necessidade durante a sessão
2. Cria o arquivo em .claude/skills/
3. Nomeia com prefixo numérico sequencial
4. Adiciona entrada neste ORCHESTRATOR.md
5. zklab-os sincroniza via webhook automaticamente