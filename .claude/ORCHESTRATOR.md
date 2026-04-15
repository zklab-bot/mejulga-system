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
Skills obrigatórias: 01 + 02 + 03
- Gerar roteiro de carrossel
- Criar novo tema para categoria
- Revisar copy de slides

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