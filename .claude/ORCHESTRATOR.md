# Orchestrator — mejulga-system

## Visão geral
Pipeline automatizado de criação e publicação de conteúdo
para o perfil @dra.julga no Instagram. Este documento define
como as skills se conectam e quando usar cada uma.

## Skills disponíveis

| Arquivo | Tipo | O que define |
|---------|------|-------------|
| `persona.md` | persona | Voz, tom, ritmo, vocabulário da Dra. Julga |
| `anti_persona.md` | persona | O que ela NÃO é (sem coach, sem moral) |
| `codigo_julgamento.md` | processo | Estrutura acusação → provas → veredicto |
| `hook_rules.md` | conteudo | 21 templates de hook (grupos V, L, C) |
| `estrutura_slides.md` | conteudo | Papel de cada um dos 7 slides |
| `visual_rules.md` | conteudo | Regras de design e tipografia |
| `legenda_rules.md` | conteudo | Estrutura e hashtags da legenda |
| `filtro_sensibilidade.md` | processo | Checklist pré-publicação |

## Ordem de leitura obrigatória
Sempre leia nessa sequência antes de qualquer tarefa:

1. `persona.md` → quem é a Dra. Julga
2. `anti_persona.md` → o que ela jamais faz
3. `codigo_julgamento.md` → estrutura do conteúdo
4. `hook_rules.md` → como capturar atenção
5. `estrutura_slides.md` → como montar o carrossel
6. `visual_rules.md` → como deve parecer
7. `legenda_rules.md` → como finalizar o post
8. `filtro_sensibilidade.md` → checklist antes de publicar

## Quando usar cada skill

### Gerar novo carrossel
Skills obrigatórias: todas (1→8 em sequência)
- Gerar roteiro completo do zero
- Adaptar tema para o tom da Dra. Julga
- Validar antes de publicar

### Revisar conteúdo existente
Skills obrigatórias: `persona.md` + `anti_persona.md` + `filtro_sensibilidade.md`
- Checar se o tom está correto
- Validar se passa no filtro de sensibilidade

### Criar novo hook
Skills obrigatórias: `persona.md` + `hook_rules.md`
- Gerar variações de abertura
- Testar templates V, L, C

### Ajustar visual
Skills obrigatórias: `visual_rules.md` + `estrutura_slides.md`
- Modificar render_slides.py
- Ajustar tipografia ou layout

### Desenvolvimento técnico
Não requer skills de conteúdo — usa CLAUDE.md diretamente
- Alterar pipeline de publicação
- Configurar GitHub Actions
- Integrar nova API

## Fluxo de sessão recomendado

### Início de sessão
1. Lê CLAUDE.md para contexto técnico
2. Lê as skills relevantes para a tarefa do dia
3. Verifica status do último workflow no GitHub Actions
4. Confirma categoria do dia na rotação das 7

### Durante a sessão
- Mantém tom da Dra. Julga em qualquer conteúdo gerado
- Aplica filtro_sensibilidade.md antes de qualquer publicação
- Registra decisões técnicas no CLAUDE.md

### Fim de sessão
1. Atualiza próximos passos no CLAUDE.md
2. Commita com mensagem descritiva
3. Confirma que webhook zklab-os sincronizou

## Estrutura de arquivos
mejulga-system/
├── CLAUDE.md
├── ORCHESTRATOR.md
├── .claude/
│   └── skills/
│       ├── persona.md
│       ├── anti_persona.md
│       ├── codigo_julgamento.md
│       ├── hook_rules.md
│       ├── estrutura_slides.md
│       ├── visual_rules.md
│       ├── legenda_rules.md
│       └── filtro_sensibilidade.md
├── content-engine/
│   └── skills/          ← cópia espelhada (fonte original)
├── render_slides.py
├── post_carrossel_instagram.py
└── .github/
└── workflows/
└── daily_post.yml

## Evolução do sistema
Quando criar nova skill:
1. Cria em `content-engine/skills/` (fonte original)
2. Espelha em `.claude/skills/`
3. Adiciona entrada neste ORCHESTRATOR.md
4. zklab-os sincroniza via webhook automaticamente